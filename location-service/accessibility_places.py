import json
import os
import urllib.error
import urllib.parse
import urllib.request

from overpass_client import (
    CATEGORY_TAGS,
    OverpassError,
    calculate_distance_meters,
)


OVERPASS_API_URL = "https://overpass.private.coffee/api/interpreter"

ACCESSIBILITY_CATEGORIES = [
    "school",
    "hospital",
    "police",
    "bank",
    "atm",
    "college",
    "restaurant",
    "park",
]


def find_accessibility_places(
    latitude: float,
    longitude: float,
    radius_meters: int,
) -> list[dict]:
    """
    Find all accessibility-related places in one Overpass request.
    """

    user_agent = os.environ.get("NOMINATIM_USER_AGENT")

    if not user_agent:
        raise OverpassError(
            "NOMINATIM_USER_AGENT environment variable is not set."
        )

    query = _build_accessibility_query(
        latitude,
        longitude,
        radius_meters,
    )

    request = urllib.request.Request(
        OVERPASS_API_URL,
        data=urllib.parse.urlencode(
            {"data": query}
        ).encode("utf-8"),
        headers={
            "User-Agent": user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=60,
        ) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as exc:
        raise OverpassError(
            f"Overpass accessibility request failed "
            f"with HTTP status {exc.code}."
        ) from exc

    except urllib.error.URLError as exc:
        raise OverpassError(
            f"Could not connect to Overpass: {exc.reason}."
        ) from exc

    except json.JSONDecodeError as exc:
        raise OverpassError(
            "Overpass returned invalid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise OverpassError(
            "Overpass returned an unexpected response format."
        )

    if "remark" in data and "elements" not in data:
        raise OverpassError(
            f"Overpass error: {data['remark']}"
        )

    elements = data.get("elements")

    if not isinstance(elements, list):
        raise OverpassError(
            "Overpass response is missing a valid 'elements' list."
        )

    return _parse_accessibility_elements(
        elements,
        latitude,
        longitude,
    )


def _build_accessibility_query(
    latitude: float,
    longitude: float,
    radius_meters: int,
) -> str:
    """
    Build one Overpass query containing all accessibility categories.
    """

    lines = []

    around = (
        f"(around:{radius_meters},{latitude},{longitude})"
    )

    for category in ACCESSIBILITY_CATEGORIES:

        tag_filters = CATEGORY_TAGS[category]

        for tag_key, tag_value in tag_filters:

            lines.append(
                f'  node["{tag_key}"="{tag_value}"]{around};'
            )

            lines.append(
                f'  way["{tag_key}"="{tag_value}"]{around};'
            )

            lines.append(
                f'  relation["{tag_key}"="{tag_value}"]{around};'
            )

    joined_lines = "\n".join(lines)

    return f"""[out:json][timeout:50];
(
{joined_lines}
);
out center;
"""


def _parse_accessibility_elements(
    elements: list,
    latitude: float,
    longitude: float,
) -> list[dict]:
    """
    Convert Overpass elements into a common place format.
    """

    places = []

    for element in elements:

        coordinates = _extract_coordinates(element)

        if coordinates is None:
            continue

        place_latitude, place_longitude = coordinates

        tags = element.get("tags", {})

        if not isinstance(tags, dict):
            tags = {}

        name = tags.get("name")

        category = _detect_category(tags)

        if category is None:
            continue

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
                "category": category,
                "distance_meters": distance_meters,
            }
        )

    return sorted(
        places,
        key=lambda place: place["distance_meters"],
    )


def _detect_category(
    tags: dict,
) -> str | None:
    """
    Detect which accessibility category an OSM element belongs to.
    """

    for category in ACCESSIBILITY_CATEGORIES:

        tag_filters = CATEGORY_TAGS[category]

        for tag_key, tag_value in tag_filters:

            if tags.get(tag_key) == tag_value:
                return category

    return None


def _extract_coordinates(
    element: dict,
) -> tuple[float, float] | None:

    if element.get("type") == "node":

        try:
            return (
                float(element["lat"]),
                float(element["lon"]),
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            return None

    center = element.get("center")

    if not isinstance(center, dict):
        return None

    try:
        return (
            float(center["lat"]),
            float(center["lon"]),
        )

    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        return None