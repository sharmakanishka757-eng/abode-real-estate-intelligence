from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI, HTTPException

from nominatim_client import NominatimError, geocode_address
from overpass_client import OverpassError, find_nearby_places
from ors_client import ORSError, get_route

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/geocode")
def geocode(address: str | None = None):
    if not address or not address.strip():
        raise HTTPException(
            status_code=400,
            detail="Address query parameter is required.",
        )

    try:
        return geocode_address(address)
    except NominatimError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/nearby")
def nearby(
    latitude: str | None = None,
    longitude: str | None = None,
    radius: str | None = None,
    category: str | None = None,
    limit: str | None = None,
):
    if (
        latitude is None
        or longitude is None
        or radius is None
        or limit is None
        or not category
        or not category.strip()
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Query parameters latitude, longitude, radius, category, and limit "
                "are required."
            ),
        )

    try:
        limit_value = int(limit)

        if limit_value <= 0:
            raise HTTPException(
               status_code=400,
                detail="Limit must be greater than 0.",
            )

        places = find_nearby_places(
            float(latitude),
            float(longitude),
            int(radius),
            category,
        )

        return places[:limit_value]

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Latitude, longitude, radius, and limit must be valid numbers.",
        ) from exc
    except OverpassError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/route")
def route(
    start_latitude: str | None = None,
    start_longitude: str | None = None,
    end_latitude: str | None = None,
    end_longitude: str | None = None,
    profile: str = "driving-car",
):
    if (
        start_latitude is None
        or start_longitude is None
        or end_latitude is None
        or end_longitude is None
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Query parameters start_latitude, start_longitude, "
                "end_latitude, and end_longitude are required."
            ),
        )

    try:
        result = get_route(
            float(start_latitude),
            float(start_longitude),
            float(end_latitude),
            float(end_longitude),
            profile,
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Latitude and longitude values must be valid numbers.",
        ) from exc

    except ORSError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )