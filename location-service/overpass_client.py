import json
import math
import os
import urllib.error
import urllib.parse
import urllib.request

OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"

SUPPORTED_CATEGORIES = {
    "hospital",
    "school",
    "college",
    "bank",
    "atm",
    "restaurant",
    "park",
    "police",
}

# Maps each category to OpenStreetMap tag key/value pairs.
CATEGORY_TAGS = {
    "hospital": [("amenity", "hospital")],
    "school": [("amenity", "school")],
    "college": [("amenity", "college"), ("amenity", "university")],
    "bank": [("amenity", "bank")],
    "atm": [("amenity", "atm")],
    "restaurant": [("amenity", "restaurant")],
    "park": [("leisure", "park")],
    "police": [("amenity", "police")],
}


class OverpassError(Exception):
    """Raised when a nearby-places query with Overpass fails."""


EARTH_RADIUS_METERS = 6_371_000


def calculate_distance_meters(
    latitude1: float,
    longitude1: float,
    latitude2: float,
    longitude2: float,
) -> float:
    """Return the straight-line distance between two points in meters."""
    lat1 = math.radians(latitude1)
    lon1 = math.radians(longitude1)
    lat2 = math.radians(latitude2)
    lon2 = math.radians(longitude2)

    delta_latitude = lat2 - lat1
    delta_longitude = lon2 - lon1

    haversine = (
        math.sin(delta_latitude / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_longitude / 2) ** 2
    )
    central_angle = 2 * math.asin(math.sqrt(haversine))

    return EARTH_RADIUS_METERS * central_angle


def find_nearby_places(
    latitude: float,
    longitude: float,
    radius_meters: int,
    category: str,
) -> list[dict]:
    """
    Find nearby OpenStreetMap places for a category using the Overpass API.

    Returns a list of places with name, latitude, longitude, and category.
    """
    _validate_inputs(latitude, longitude, radius_meters, category)

    user_agent = os.environ.get("NOMINATIM_USER_AGENT")
    if not user_agent:
        raise OverpassError(
            "NOMINATIM_USER_AGENT environment variable is not set."
        )

    query = _build_query(latitude, longitude, radius_meters, category)
    request = urllib.request.Request(
        OVERPASS_API_URL,
        data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
        headers={
            "User-Agent": user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise OverpassError(
            f"Overpass request failed with HTTP status {exc.code}."
        ) from exc
    except urllib.error.URLError as exc:
        raise OverpassError(
            f"Could not connect to Overpass: {exc.reason}."
        ) from exc
    except json.JSONDecodeError as exc:
        raise OverpassError("Overpass returned invalid JSON.") from exc

    if not isinstance(data, dict):
        raise OverpassError("Overpass returned an unexpected response format.")

    if "remark" in data and "elements" not in data:
        raise OverpassError(f"Overpass error: {data['remark']}")

    elements = data.get("elements")
    if not isinstance(elements, list):
        raise OverpassError("Overpass response is missing a valid 'elements' list.")

    return _parse_elements(elements, category, latitude, longitude)


def _validate_inputs(
    latitude: float,
    longitude: float,
    radius_meters: int,
    category: str,
) -> None:
    try:
        latitude = float(latitude)
        longitude = float(longitude)
        radius_meters = int(radius_meters)
    except (TypeError, ValueError) as exc:
        raise OverpassError("Latitude, longitude, and radius must be numbers.") from exc

    if not -90 <= latitude <= 90:
        raise OverpassError("Latitude must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise OverpassError("Longitude must be between -180 and 180.")

    if radius_meters <= 0:
        raise OverpassError("Radius must be a positive number of meters.")

    if not category or not category.strip():
        raise OverpassError("Category must not be empty.")

    normalized_category = category.strip().lower()
    if normalized_category not in SUPPORTED_CATEGORIES:
        supported = ", ".join(sorted(SUPPORTED_CATEGORIES))
        raise OverpassError(
            f"Unsupported category '{category}'. Supported categories: {supported}."
        )


def _build_query(
    latitude: float,
    longitude: float,
    radius_meters: int,
    category: str,
) -> str:
    normalized_category = category.strip().lower()
    tag_filters = CATEGORY_TAGS[normalized_category]

    lines = []
    for tag_key, tag_value in tag_filters:
        around = f"(around:{radius_meters},{latitude},{longitude})"
        lines.append(f'  node["{tag_key}"="{tag_value}"]{around};')
        lines.append(f'  way["{tag_key}"="{tag_value}"]{around};')
        lines.append(f'  relation["{tag_key}"="{tag_value}"]{around};')

    joined_lines = "\n".join(lines)
    return f"""[out:json][timeout:25];
(
{joined_lines}
);
out center;
"""


def _parse_elements(
    elements: list,
    category: str,
    latitude: float,
    longitude: float,
) -> list[dict]:
    places = []
    normalized_category = category.strip().lower()

    for element in elements:
        coordinates = _extract_coordinates(element)
        if coordinates is None:
            continue

        place_latitude, place_longitude = coordinates
        tags = element.get("tags", {})
        name = tags.get("name")
        distance_meters = round(
            calculate_distance_meters(
                latitude,
                longitude,
                place_latitude,
                place_longitude,
            ),
            2,
        )

        places.append(
            {
                "name": name,
                "latitude": place_latitude,
                "longitude": place_longitude,
                "category": normalized_category,
                "distance_meters": distance_meters,
            }
        )

    return sorted(places, key=lambda place: place["distance_meters"])


def _extract_coordinates(element: dict) -> tuple[float, float] | None:
    if element.get("type") == "node":
        try:
            return float(element["lat"]), float(element["lon"])
        except (KeyError, TypeError, ValueError):
            return None

    center = element.get("center")
    if not isinstance(center, dict):
        return None

    try:
        return float(center["lat"]), float(center["lon"])
    except (KeyError, TypeError, ValueError):
        return None
