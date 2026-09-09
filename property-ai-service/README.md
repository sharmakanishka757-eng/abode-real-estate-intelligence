# Property AI Service

Member 3 service for the ABODE Real Estate Intelligence project.

This service stores property listings and will later support property analysis
and AI-based intelligence. This milestone covers the FastAPI foundation and
CRUD API only. AI/ML is not implemented yet.

## Technology

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL

## Folder structure

```text
property-ai-service/
    app/
        main.py              # FastAPI app, health check, startup table creation
        database.py          # SQLAlchemy engine, session, and FastAPI dependency
        models/property.py   # Property database model
        schemas/property.py  # Pydantic create, update, and response schemas
        routes/properties.py # REST routes for /properties
        services/            # Reserved for later analysis / AI logic
    requirements.txt
    .env.example
    Dockerfile
    README.md
```

## Install dependencies

From this directory:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure DATABASE_URL

1. Copy `.env.example` to `.env`.
2. Set `DATABASE_URL` to your PostgreSQL connection string:

```text
DATABASE_URL=postgresql://username:password@localhost:5432/abode
```

Do not commit `.env` or real passwords.

The database must exist before the service starts. On startup the service
creates the `properties` table if it is missing.

## Run the FastAPI application

From `property-ai-service/`:

```bash
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

Interactive docs: `http://127.0.0.1:8000/docs`.

## Available endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/health` | Service health check |
| POST | `/properties` | Create a property listing |
| GET | `/properties` | List all property listings |
| GET | `/properties/{property_id}` | Get one property listing |
| PUT | `/properties/{property_id}` | Update a property listing |
| DELETE | `/properties/{property_id}` | Delete a property listing |

Example health response:

```json
{
  "status": "ok",
  "service": "property-ai-service"
}
```
