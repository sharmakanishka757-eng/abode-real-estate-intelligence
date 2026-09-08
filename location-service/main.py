from fastapi import FastAPI, HTTPException

from nominatim_client import NominatimError, geocode_address

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
