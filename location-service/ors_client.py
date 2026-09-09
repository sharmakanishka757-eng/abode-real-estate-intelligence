import json
import os
import urllib.error
import urllib.parse
import urllib.request


ORS_DIRECTIONS_URL = (
    "https://api.heigit.org/openrouteservice/v2/directions"
)


class ORSError(Exception):
    """Raised when routing with OpenRouteService fails."""


def get_route(
    start_latitude: float,
    start_longitude: float,
    end_latitude: float,
    end_longitude: float,
    profile: str = "driving-car",
) -> dict:
    api_key = os.environ.get("OPENROUTESERVICE_API_KEY")

    if not api_key:
        raise ORSError(
            "OPENROUTESERVICE_API_KEY environment variable is not set."
        )

    allowed_profiles = {
        "driving-car",
        "foot-walking",
        "cycling-regular",
    }

    if profile not in allowed_profiles:
        raise ORSError(
            f"Unsupported routing profile '{profile}'. "
            f"Supported profiles: {', '.join(sorted(allowed_profiles))}."
        )

    
    params = urllib.parse.urlencode(
        {
            "api_key": api_key,
            "start": f"{start_longitude},{start_latitude}",
            "end": f"{end_longitude},{end_latitude}",
        }
    )

    url = f"{ORS_DIRECTIONS_URL}/{profile}?{params}"

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/geo+json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:
            error_body = ""

        raise ORSError(
            f"OpenRouteService request failed with HTTP status "
            f"{exc.code}. {error_body}"
        ) from exc

    except urllib.error.URLError as exc:
        raise ORSError(
            f"Could not connect to OpenRouteService: {exc.reason}."
        ) from exc

    except json.JSONDecodeError as exc:
        raise ORSError(
            "OpenRouteService returned invalid JSON."
        ) from exc

    try:
        feature = data["features"][0]
        summary = feature["properties"]["summary"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ORSError(
            "OpenRouteService response does not contain a valid route."
        ) from exc

    return {
        "distance_meters": round(summary["distance"], 2),
        "duration_seconds": round(summary["duration"], 2),
        "duration_minutes": round(summary["duration"] / 60, 2),
    }