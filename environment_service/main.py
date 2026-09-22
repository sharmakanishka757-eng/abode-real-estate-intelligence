from fastapi import FastAPI

from environment_service.weather_client import get_weather
from environment_service.aqi_client import get_aqi_by_coordinates


app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/weather")
def weather(latitude: float, longitude: float):
    return get_weather(latitude, longitude)


@app.get("/aqi")
def aqi(latitude: float, longitude: float):
    return get_aqi_by_coordinates(latitude, longitude)