# ABODE Real Estate Intelligence

A smart real-estate intelligence platform designed to help property buyers
understand properties and their surrounding neighborhood before making a
decision.

## Project Architecture

The project is organized as a multi-service application:

- `frontend/` — User interface
- `api-gateway/` — Entry point for frontend API requests
- `location-service/` — Location and nearby-place intelligence
- `environment-service/` — Environmental and neighborhood data
- `property-ai-service/` — Property analysis and AI-based intelligence
- `database/` — Database-related configuration and resources
- `docs/` — Project documentation

## Team Responsibilities

### Member 1 — Location Intelligence
Responsible for:

- Geocoding
- Coordinates
- OpenStreetMap data
- Nearby places
- Distance and routing
- Travel time
- Public transport information
- Accessibility scoring
- PostGIS spatial queries

### Member 2 — Environment Intelligence
Responsible for environmental and neighborhood-related data.

### Member 3 — Property & AI Intelligence
Responsible for property-related functionality and AI-based analysis.

## Technology Stack

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Python
- FastAPI

### Database
- PostgreSQL
- PostGIS

### Geographic Data
- OpenStreetMap
- Nominatim
- Overpass API

### Routing & Transport
- OpenRouteService or approved routing provider
- GTFS where applicable

## Development

The project is developed incrementally using separate services and Git
branches for each team member.

The `main` branch should contain stable, integrated code.

## Environment Variables

Actual secrets and API keys must never be committed to GitHub.

Use `.env.example` as the template for required environment variables.

## Project Status

🚧 Under active development.