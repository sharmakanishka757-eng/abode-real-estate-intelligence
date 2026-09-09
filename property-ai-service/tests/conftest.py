"""Test fixtures. Uses a temporary SQLite database when PostgreSQL is not configured."""

import os
from pathlib import Path

TEST_DB = Path(__file__).resolve().parent / "test.sqlite3"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.models.preferences import UserPreference  # noqa: F401
from app.models.property import Property  # noqa: F401


@pytest.fixture()
def client() -> TestClient:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


def create_sample_property(client: TestClient, **overrides) -> dict:
    payload = {
        "title": "Sample apartment",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 20000,
        "address": "Vaishali Nagar",
        "city": "Jaipur",
        "latitude": 26.9126,
        "longitude": 75.7435,
        "area": 900,
        "bedrooms": 2,
        "bathrooms": 2,
        "description": "Test listing",
    }
    payload.update(overrides)
    response = client.post("/properties", json=payload)
    assert response.status_code == 201, response.text
    return response.json()
