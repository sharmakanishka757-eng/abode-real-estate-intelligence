# Property AI Service

Member 3 service for the ABODE Real Estate Intelligence project.

This service stores property listings, searches them, and scores them against
user preferences with a deterministic rule-based engine. Location and
environment scores come from an integration layer. Today that layer uses
deterministic mocks (or explicit request overrides). It is built so Member 1
and Member 2 can later connect without rewriting the scoring engine. LLM/AI
recommendation generation is a future milestone.

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
        models/preferences.py  # User preference profile
        schemas/property.py  # Pydantic create, update, search, and response schemas
        schemas/preferences.py  # Preference create/update/response schemas
        schemas/scoring.py   # Analyze request, location/environment score schemas
        schemas/intelligence.py  # Location/environment intelligence contracts
        routes/properties.py # REST routes for /properties and /properties/search
        routes/preferences.py  # Preference CRUD
        routes/analysis.py   # POST /properties/{id}/analyze
        services/property_search.py  # SQLAlchemy search filters
        services/preference_weights.py  # Category weight normalization
        services/property_scoring.py  # Rule-based match score and explanations
        services/intelligence_integration.py  # Location/environment boundary (mock today)
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
creates the `properties` and `user_preferences` tables if they are missing.

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
| POST | `/properties/{property_id}/analyze` | Personalized match score for a listing |
| POST | `/preferences` | Create a user preference profile |
| GET | `/preferences/{user_id}` | Get one user's preferences |
| PUT | `/preferences/{user_id}` | Update one user's preferences |
| DELETE | `/preferences/{user_id}` | Delete one user's preferences |

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

## User preferences

Each `user_id` has one preference profile in this milestone. There is no
authentication yet; `user_id` is a client-supplied string.

| Method | Path | Description |
| ------ | ---- | ----------- |
| POST | `/preferences` | Create preferences (`201`, or `409` if that user already has a profile) |
| GET | `/preferences/{user_id}` | Fetch preferences |
| PUT | `/preferences/{user_id}` | Partial update |
| DELETE | `/preferences/{user_id}` | Delete preferences |

Stored fields include budget range, preferred listing type (`buy` / `rent`),
preferred property types (`apartment`, `house`, `land`), optional minimum
bedrooms/area, and category priority weights:

- `safety_weight`
- `transport_weight`
- `healthcare_weight`
- `education_weight`
- `environment_weight`
- `water_utilities_weight`
- `flood_risk_weight`
- `amenities_weight`
- `noise_connectivity_weight`

Weights are priorities, not percentages. They do not need to sum to 100. The
scoring engine normalizes them (for example 5, 3, 2 → 0.5, 0.3, 0.2). Each
weight must be between 0 and 10. At least one weight must be greater than zero.

## Personalized scoring

`POST /properties/{property_id}/analyze` scores a listing against the request
body. The engine is **deterministic and rule-based**. It is designed so real
Location Intelligence and Environment Intelligence services can be plugged in
later. It does **not** call those services, and it does **not** use an LLM.

Request body:

```json
{
  "user_preferences": {
    "min_budget": 10000,
    "max_budget": 25000,
    "preferred_listing_type": "rent",
    "preferred_property_types": ["apartment"],
    "min_bedrooms": 2,
    "min_area": 800,
    "safety_weight": 5,
    "transport_weight": 3,
    "healthcare_weight": 2,
    "education_weight": 1,
    "environment_weight": 1,
    "water_utilities_weight": 1,
    "flood_risk_weight": 2,
    "amenities_weight": 1,
    "noise_connectivity_weight": 1
  },
  "location_scores": {
    "safety": 90,
    "transport": 85,
    "healthcare": 80,
    "education": 70,
    "amenities": 88,
    "noise_connectivity": 75
  },
  "environment_scores": {
    "environment": 80,
    "water_utilities": 65,
    "flood_risk": 90
  }
}
```

`location_scores` and `environment_scores` are optional. If you send them, the
analyze endpoint uses those values (useful in tests). If you omit them, the
**integration layer** supplies deterministic mock intelligence. Every category
value must be between 0 and 100. For `flood_risk`, **100 means low risk /
favorable** and **0 means high risk / unfavorable**.

**Mock intelligence is used only for development/testing. It is not real
location or environmental data.**

The match score is 0–100 (two decimal places) and combines:

- Budget, listing type, property type, bedrooms, and area compatibility
- Weighted location/environment category scores using normalized preferences

Recommendation labels:

| Score | Label |
| ----- | ----- |
| 90–100 | Excellent Match |
| 75–89.99 | Good Match |
| 60–74.99 | Moderate Match |
| below 60 | Low Match |

Explanations (`summary`, `positive_factors`, `caution_factors`) are generated
from the same rules. They are not AI-generated.

The response includes the existing `PropertyResponse` object plus scoring
fields. Example:

```json
{
  "property_id": 1,
  "match_score": 87.50,
  "recommendation": "Good Match",
  "summary": "Good overall match based on your selected preferences.",
  "positive_factors": [
    "Property fits within your preferred budget.",
    "Property meets your minimum bedroom requirement.",
    "Transport is a strong match."
  ],
  "caution_factors": [
    "Environment score is relatively low and may require further consideration."
  ],
  "category_scores": {
    "safety": 90,
    "transport": 85,
    "healthcare": 80
  }
}
```

## Location and environment integration

Member 3 scoring does not call other services yet. Analyze uses
`app/services/intelligence_integration.py` as the only boundary:

```text
analyze route
    → resolve_intelligence()   (explicit scores or mock)
    → property_scoring.py      (unchanged match algorithm)
    → recommendation + explanation
```

| Source | When it is used |
| ------ | --------------- |
| Explicit `location_scores` / `environment_scores` in the request | Always preferred when present |
| Deterministic mock from the integration layer | When that block is omitted |

The mock is derived from the property's city and coordinates so the same
listing always gets the same scores. It is **not** random and **not** real
neighborhood data.

### Score meaning

For every category, **0 = unfavorable** and **100 = favorable**.

`flood_risk` uses the same direction: **100 = low flood/waterlogging risk**,
**0 = high risk**.

### Future service contracts

These contracts are documentation only. This milestone does **not** implement
HTTP clients.

Member 1 — Location Intelligence:

```text
GET /api/location/{property_id}
```

```json
{
  "property_id": 123,
  "scores": {
    "safety": 85,
    "transport": 78,
    "healthcare": 90,
    "education": 75,
    "amenities": 88,
    "noise_connectivity": 72
  }
}
```

Member 2 — Environment Intelligence:

```text
GET /api/environment/{property_id}
```

```json
{
  "property_id": 123,
  "scores": {
    "environment": 80,
    "water_utilities": 75,
    "flood_risk": 90
  }
}
```

When those APIs exist, only `intelligence_integration.py` should change.
`property_scoring.py` should keep receiving the same structured scores.

## Tests

From `property-ai-service/`:

```bash
pytest
```

Tests use a temporary SQLite database and do not require PostgreSQL.
