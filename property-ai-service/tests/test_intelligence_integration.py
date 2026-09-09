"""Tests for the location/environment intelligence integration layer."""

import pytest
from pydantic import ValidationError

from app.schemas.intelligence import (
    EnvironmentIntelligence,
    LocationIntelligence,
    PropertyIntelligenceInput,
)
from app.schemas.scoring import EnvironmentScores, LocationScores
from app.services.intelligence_integration import (
    get_environment_intelligence,
    get_location_intelligence,
    resolve_intelligence,
)
from tests.conftest import create_sample_property
from tests.test_preferences_and_analyze import analyze_payload


SAMPLE_PROPERTY = PropertyIntelligenceInput(
    id=1,
    city="Jaipur",
    latitude=26.9126,
    longitude=75.7435,
    address="Vaishali Nagar",
    property_type="apartment",
    listing_type="rent",
)


def test_valid_location_intelligence_structure():
    location = get_location_intelligence(SAMPLE_PROPERTY)
    assert set(location.model_dump()) == {
        "safety",
        "transport",
        "healthcare",
        "education",
        "amenities",
        "noise_connectivity",
    }


def test_valid_environment_intelligence_structure():
    environment = get_environment_intelligence(SAMPLE_PROPERTY)
    assert set(environment.model_dump()) == {
        "environment",
        "water_utilities",
        "flood_risk",
    }


def test_intelligence_score_range_validation():
    location = get_location_intelligence(SAMPLE_PROPERTY)
    environment = get_environment_intelligence(SAMPLE_PROPERTY)
    for value in location.model_dump().values():
        assert 0 <= value <= 100
    for value in environment.model_dump().values():
        assert 0 <= value <= 100

    with pytest.raises(ValidationError):
        LocationIntelligence(
            safety=150,
            transport=80,
            healthcare=80,
            education=80,
            amenities=80,
            noise_connectivity=80,
        )
    with pytest.raises(ValidationError):
        EnvironmentIntelligence(environment=80, water_utilities=80, flood_risk=-1)


def test_deterministic_mock_behavior():
    first = get_location_intelligence(SAMPLE_PROPERTY)
    second = get_location_intelligence(SAMPLE_PROPERTY)
    assert first == second
    assert get_environment_intelligence(SAMPLE_PROPERTY) == get_environment_intelligence(
        SAMPLE_PROPERTY
    )

    other_city = SAMPLE_PROPERTY.model_copy(update={"city": "Ajmer", "latitude": 26.45})
    assert get_location_intelligence(other_city) != first


def test_explicit_location_score_override():
    explicit = LocationScores(safety=95, transport=90, healthcare=85)
    resolved = resolve_intelligence(
        SAMPLE_PROPERTY,
        location_scores=explicit,
        environment_scores=None,
    )
    assert resolved.location_source == "explicit"
    assert resolved.environment_source == "mock"
    assert resolved.location_scores().safety == 95
    assert resolved.location_scores().transport == 90


def test_explicit_environment_score_override():
    explicit = EnvironmentScores(environment=85, water_utilities=80, flood_risk=95)
    resolved = resolve_intelligence(
        SAMPLE_PROPERTY,
        location_scores=None,
        environment_scores=explicit,
    )
    assert resolved.environment_source == "explicit"
    assert resolved.location_source == "mock"
    assert resolved.environment_scores().flood_risk == 95
    assert resolved.environment_scores().environment == 85


def test_analyze_endpoint_without_explicit_intelligence_scores(client):
    property_item = create_sample_property(client, city="Jaipur")
    payload = analyze_payload()
    payload.pop("location_scores")
    payload.pop("environment_scores")

    response = client.post(
        f"/properties/{property_item['id']}/analyze",
        json=payload,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert 0 <= body["match_score"] <= 100
    assert body["category_scores"]
    mock_input = PropertyIntelligenceInput(
        city="Jaipur",
        latitude=property_item["latitude"],
        longitude=property_item["longitude"],
    )
    mock_location = get_location_intelligence(mock_input)
    mock_environment = get_environment_intelligence(mock_input)
    assert body["category_scores"]["safety"] == mock_location.safety
    assert body["category_scores"]["flood_risk"] == mock_environment.flood_risk


def test_analyze_endpoint_with_explicit_intelligence_scores(client):
    property_item = create_sample_property(client)
    response = client.post(
        f"/properties/{property_item['id']}/analyze",
        json=analyze_payload(),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["category_scores"]["transport"] == 85
    assert body["category_scores"]["flood_risk"] == 90
