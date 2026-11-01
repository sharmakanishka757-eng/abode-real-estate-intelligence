from fastapi import FastAPI

from environment_service.weather_client import get_weather
from environment_service.aqi_client import get_aqi_by_coordinates
from environment_service.crime_api import router as crime_router
from environment_service.water_supply_api import router as water_supply_router


app = FastAPI(
    title="ABODE Environment Intelligence API",
    description=(
        "Weather, Air Quality, Crime and "
        "Water Supply Intelligence services"
    ),
    version="1.1.0"
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/weather")
def weather(latitude: float, longitude: float):
    return get_weather(latitude, longitude)


@app.get("/aqi")
def aqi(latitude: float, longitude: float):
    return get_aqi_by_coordinates(latitude, longitude)


# Register Crime Intelligence routes.
app.include_router(crime_router)

# Register Water Supply Intelligence routes.
app.include_router(water_supply_router)
