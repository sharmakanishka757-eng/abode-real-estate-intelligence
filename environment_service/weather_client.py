import requests

from environment_service.database import get_connection


def get_weather(latitude: float, longitude: float) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "timezone": "Asia/Kolkata",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    current = data["current"]

    weather_data = {
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
        "weather_code": current["weather_code"],
        "timestamp": current["time"],
        "source": "Open-Meteo",
    }

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO weather (
                    latitude,
                    longitude,
                    temperature,
                    humidity,
                    wind_speed,
                    weather_code,
                    recorded_at,
                    source
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    latitude,
                    longitude,
                    weather_data["temperature"],
                    weather_data["humidity"],
                    weather_data["wind_speed"],
                    weather_data["weather_code"],
                    weather_data["timestamp"],
                    weather_data["source"],
                ),
            )

        connection.commit()

    finally:
        connection.close()

    return {
        **weather_data,
        "latitude": latitude,
        "longitude": longitude,
    }