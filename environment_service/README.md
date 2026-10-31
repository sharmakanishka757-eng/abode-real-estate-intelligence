# Environment & Public Data Service

This service provides weather and air-quality information based on geographical coordinates. It is built using FastAPI and stores air-quality observations in PostgreSQL.

## Base URL

Local development:

`http://127.0.0.1:8002`

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

Checks whether the Environment Service is running.

**Response:**
```json
{
  "status": "ok"
}
```

**HTTP Status:** `200 OK`

### 2. Weather Information

**Endpoint:** `GET /weather`

Fetches weather information for the supplied geographical coordinates.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| latitude | number | Yes | Geographic latitude |
| longitude | number | Yes | Geographic longitude |

**Example Request:**

`GET /weather?latitude=26.9124&longitude=75.7873`

**Example Response:**
```json
{
  "temperature": 28,
  "humidity": 46,
  "wind_speed": 4.6,
  "weather_code": 0,
  "timestamp": "2026-10-31T14:45",
  "source": "Open-Meteo",
  "latitude": 26.9124,
  "longitude": 75.7873
}
```

**HTTP Status:** `200 OK`

### 3. Air Quality Information

**Endpoint:** `GET /aqi`

Fetches air-quality information using the nearest available monitoring station for the supplied coordinates.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| latitude | number | Yes | Geographic latitude |
| longitude | number | Yes | Geographic longitude |

**Example Request:**

`GET /aqi?latitude=26.9124&longitude=75.7873`

**Response Structure:**

| Section | Description |
|---|---|
| location | Requested coordinates |
| time_window | Start and end of the observation window |
| station | Selected monitoring station and its location |
| aqi | Overall AQI, category and dominant pollutant |
| pollutants | Individual pollutant measurements and data-quality information |

**Pollutants currently returned:**

- PM10 (`pm10`)
- PM2.5 (`pm25`)
- Nitrogen Dioxide (`no2`)
- Sulphur Dioxide (`so2`)
- Carbon Monoxide (`co`)
- Ozone (`o3`)

**Pollutant response fields:**

| Field | Description |
|---|---|
| status | Data completeness status |
| records_found | Number of records found |
| required_hours | Required observation hours |
| average_coverage | Coverage value reported by the pipeline |
| duplicates_removed | Number of duplicate records removed |
| invalid_timestamps | Number of invalid timestamps |
| average | Calculated pollutant average |
| unit | Measurement unit |
| sub_index | Individual pollutant AQI sub-index |

**Example overall AQI response section:**
```json
{
  "aqi": {
    "aqi": 72,
    "category": "Satisfactory",
    "dominant_pollutant": "so2"
  }
}
```

**HTTP Status:** `200 OK`

### Validation Errors

The `/weather` and `/aqi` endpoints require both latitude and longitude.

FastAPI returns `422 Unprocessable Entity` when request validation fails, such as when required parameters are missing or invalid.

## Data Sources

| Data | Provider |
|---|---|
| Weather | Open-Meteo |
| Air Quality | OpenAQ |

## Technology Stack

- Python
- FastAPI
- PostgreSQL
- Docker
- Open-Meteo API
- OpenAQ API

## Local Development

Start the service from the project root:

```powershell
uvicorn environment_service.main:app --port 8002 --reload
```

Open the interactive API documentation:

`http://127.0.0.1:8002/docs`

## Database

The service stores air-quality observations in the PostgreSQL `air_quality` table.

The table includes station information, coordinates, AQI, pollutant averages, observation timestamp and data source.

A unique constraint on `(station_id, recorded_at)` prevents duplicate observations for the same station and timestamp. Existing observations are updated when a matching record is inserted again.