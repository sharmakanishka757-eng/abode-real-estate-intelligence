# Property AI Service

Member 3 service for the ABODE Real Estate Intelligence project.

This service stores property listings and will later support property analysis
and AI-based intelligence. The current milestones cover the FastAPI foundation,
CRUD API, and property search. AI/ML is not implemented yet.

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
        schemas/property.py  # Pydantic create, update, search, and response schemas
        routes/properties.py # REST routes for /properties and /properties/search
        services/property_search.py  # SQLAlchemy search filters
    scripts/seed_data.py     # Demo listings for local development
    tests/                   # Search and API tests
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
| GET | `/properties/search` | Search listings with optional filters |
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

## Property search

`GET /properties/search` filters listings in the database. Every query
parameter is optional. Combining parameters applies all of them together.
City matching is case-insensitive. An empty result is HTTP 200 with
`"results": []`, not 404.

Supported filters:

| Parameter | Meaning |
| --------- | ------- |
| `city` | Case-insensitive city match |
| `listing_type` | `buy` or `rent` |
| `property_type` | `apartment`, `house`, or `land` |
| `min_price` | Price greater than or equal to this value |
| `max_price` | Price less than or equal to this value |
| `min_bedrooms` | Bedrooms greater than or equal to this value |
| `max_bedrooms` | Bedrooms less than or equal to this value |
| `min_area` | Area greater than or equal to this value |
| `max_area` | Area less than or equal to this value |
| `skip` | Number of matching rows to skip (default 0) |
| `limit` | Page size (default 20, maximum 100) |

Example requests:

```text
GET /properties/search?city=Jaipur
GET /properties/search?city=Jaipur&listing_type=rent
GET /properties/search?city=Jaipur&property_type=apartment&max_price=25000
GET /properties/search?city=Jaipur&listing_type=buy&min_bedrooms=2
GET /properties/search?city=Jaipur&property_type=apartment&max_price=25000&min_bedrooms=2
```

Example response:

```json
{
  "total": 3,
  "skip": 0,
  "limit": 20,
  "results": [
    {
      "id": 1,
      "title": "2BHK apartment in Vaishali Nagar",
      "property_type": "apartment",
      "listing_type": "rent",
      "price": 18000.00,
      "city": "Jaipur"
    }
  ]
}
```

Each item in `results` uses the same `PropertyResponse` fields as the CRUD
endpoints.

## Demo seed data

The seed script inserts about 10 fictional Jaipur-area listings so search can
be tried locally. **This is development/demo data only.** It is not real
inventory and should not be treated as actual prices or availability.

From `property-ai-service/`:

```bash
python scripts/seed_data.py
```

The script uses the same `DATABASE_URL` as the API. Running it again skips
titles that already exist, so it does not duplicate the same demo rows.

## Tests

From `property-ai-service/`:

```bash
pytest
```

Tests use a temporary SQLite database and do not require PostgreSQL.
