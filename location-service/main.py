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
        start_latitude_value = float(start_latitude)
        start_longitude_value = float(start_longitude)
        end_latitude_value = float(end_latitude)
        end_longitude_value = float(end_longitude)

        if not -90 <= start_latitude_value <= 90:
            raise HTTPException(
                status_code=400,
                detail="Start latitude must be between -90 and 90.",
            )

        if not -180 <= start_longitude_value <= 180:
            raise HTTPException(
                status_code=400,
                detail="Start longitude must be between -180 and 180.",
            )

        if not -90 <= end_latitude_value <= 90:
            raise HTTPException(
                status_code=400,
                detail="End latitude must be between -90 and 90.",
            )

        if not -180 <= end_longitude_value <= 180:
            raise HTTPException(
                status_code=400,
                detail="End longitude must be between -180 and 180.",
            )

        result = get_route(
            start_latitude_value,
            start_longitude_value,
            end_latitude_value,
            end_longitude_value,
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

@app.get("/travel-time")
def travel_time(
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
        start_latitude_value = float(start_latitude)
        start_longitude_value = float(start_longitude)
        end_latitude_value = float(end_latitude)
        end_longitude_value = float(end_longitude)

        if not -90 <= start_latitude_value <= 90:
            raise HTTPException(
                status_code=400,
                detail="Start latitude must be between -90 and 90.",
            )

        if not -180 <= start_longitude_value <= 180:
            raise HTTPException(
                status_code=400,
                detail="Start longitude must be between -180 and 180.",
            )

        if not -90 <= end_latitude_value <= 90:
            raise HTTPException(
                status_code=400,
                detail="End latitude must be between -90 and 90.",
            )

        if not -180 <= end_longitude_value <= 180:
            raise HTTPException(
                status_code=400,
                detail="End longitude must be between -180 and 180.",
            )

        result = get_route(
            start_latitude_value,
            start_longitude_value,
            end_latitude_value,
            end_longitude_value,
            profile,
        )

        return {
            "distance_km": round(result["distance_meters"] / 1000, 2),
            "duration_minutes": result["duration_minutes"],
            "profile": profile,
        }

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