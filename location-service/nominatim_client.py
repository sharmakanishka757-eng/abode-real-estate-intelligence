import json
import os
import urllib.error
import urllib.parse
import urllib.request

NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"


class NominatimError(Exception):
    """Raised when geocoding with Nominatim fails."""


def geocode_address(address: str) -> dict:
    """
    Geocode an address using the public Nominatim search API.

    Returns a dict with latitude, longitude, and display_name (if available).
    """
    if not address or not address.strip():
        raise NominatimError("Address must not be empty.")

    user_agent = os.environ.get("NOMINATIM_USER_AGENT")
    if not user_agent:
        raise NominatimError(
            "NOMINATIM_USER_AGENT environment variable is not set."
        )

    params = urllib.parse.urlencode(
        {
            "q": address.strip(),
            "format": "json",
            "limit": 1,
        }
    )
    url = f"{NOMINATIM_SEARCH_URL}?{params}"

    request = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent},
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise NominatimError(
            f"Nominatim request failed with HTTP status {exc.code}."
        ) from exc
    except urllib.error.URLError as exc:
        raise NominatimError(
            f"Could not connect to Nominatim: {exc.reason}."
        ) from exc
    except json.JSONDecodeError as exc:
        raise NominatimError("Nominatim returned invalid JSON.") from exc

    if not data:
        raise NominatimError(f"No results found for address: {address.strip()}")

    result = data[0]

    try:
        latitude = float(result["lat"])
        longitude = float(result["lon"])
    except (KeyError, TypeError, ValueError) as exc:
        raise NominatimError(
            "Nominatim result is missing valid latitude or longitude."
        ) from exc

    display_name = result.get("display_name")

    return {
        "latitude": latitude,
        "longitude": longitude,
        "display_name": display_name,
    }
