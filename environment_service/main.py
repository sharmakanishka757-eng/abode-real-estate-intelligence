from fastapi import FastAPI
from environment_service.weather_client import get_weather

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/weather")
def weather(latitude: float, longitude: float):
    return get_weather(latitude, longitude)