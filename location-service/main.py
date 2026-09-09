from fastapi import FastAPI, HTTPException

from nominatim_client import NominatimError, geocode_address
from overpass_client import OverpassError, find_nearby_places

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