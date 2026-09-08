# Location Service

This service provides **location intelligence** for the ABODE Real Estate Intelligence platform. It helps users understand where a property is and what surrounds it.

## Planned Responsibilities

The following capabilities are planned for this service:

- Address geocoding
- Latitude and longitude
- OpenStreetMap data
- Nearby places
- Distance and routing
- Travel time
- Public transport information
- Accessibility scoring
- PostGIS spatial queries

These features will be implemented **incrementally**, one step at a time.

## Current Endpoints

### Health check

```
GET /health
```

**Response:**

```json
{"status": "ok"}
```

## Technology

This service is built with **FastAPI** and runs with **Uvicorn**.

## Running the Service

From the `location-service` directory:

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Start the server:

   ```bash
   uvicorn main:app --reload
   ```

3. Open `http://127.0.0.1:8000/health` in your browser or use a tool like `curl` to verify the service is running.
