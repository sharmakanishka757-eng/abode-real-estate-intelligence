"""Unit tests for preference weight normalization and property scoring."""

import pytest
from pydantic import ValidationError

from app.schemas.preferences import PreferenceScoringInput
from app.schemas.scoring import EnvironmentScores, LocationScores
from app.services.preference_weights import (
    ZeroCategoryWeightError,
    normalize_category_weights,
)
from app.services.property_scoring import (
    EXCELLENT_MATCH_MIN,
    GOOD_MATCH_MIN,
    MODERATE_MATCH_MIN,
    recommendation_from_score,
    score_area,
    score_bedrooms,
    score_budget,
    score_categories,
    score_listing_type,
    score_property,
    score_property_type,
)


def make_preferences(**overrides) -> PreferenceScoringInput:
    payload = {
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
        "flood_risk_weight": 1,
        "amenities_weight": 1,
        "noise_connectivity_weight": 1,
    }
    payload.update(overrides)
    return PreferenceScoringInput(**payload)


def test_perfect_budget_match():
    assert score_budget(18000, 10000, 25000) == 100


def test_budget_mismatch():
    assert score_budget(80000, 10000, 25000) == 0
    assert score_budget(9000, 10000, 25000) == 50


def test_listing_type_match():
    assert score_listing_type("rent", "rent") == 100
    assert score_listing_type("buy", "rent") == 0


def test_property_type_match():
    assert score_property_type("apartment", ["apartment", "house"]) == 100
    assert score_property_type("land", ["apartment"]) == 0


def test_bedroom_requirement():
    assert score_bedrooms(2, 2) == 100
    assert score_bedrooms(3, 2) == 100
    assert score_bedrooms(1, 2) == 40
    assert score_bedrooms(0, 2) == 0
    assert score_bedrooms(None, 2) == 0
    assert score_bedrooms(1, None) == 100


def test_area_requirement():
    assert score_area(900, 800) == 100
    assert score_area(760, 800) == 50
    assert score_area(500, 800) == 0
    assert score_area(None, 800) == 0
    assert score_area(100, None) == 100


def test_weight_normalization():
    normalized = normalize_category_weights(
        {"safety": 5, "transport": 3, "healthcare": 2}
    )
    assert normalized["safety"] == pytest.approx(0.5)
    assert normalized["transport"] == pytest.approx(0.3)
    assert normalized["healthcare"] == pytest.approx(0.2)
    assert sum(normalized.values()) == pytest.approx(1.0)


def test_zero_weight_validation():
    with pytest.raises(ZeroCategoryWeightError):
        normalize_category_weights({"safety": 0, "transport": 0})
    with pytest.raises(ValidationError):
        make_preferences(
            safety_weight=0,
            transport_weight=0,
            healthcare_weight=0,
            education_weight=0,
            environment_weight=0,
            water_utilities_weight=0,
            flood_risk_weight=0,
            amenities_weight=0,
            noise_connectivity_weight=0,
        )


def test_location_environment_weighted_scoring():
    weighted = score_categories(
        {"safety": 5, "transport": 5, "environment": 0, "flood_risk": 0},
        {"safety": 100, "transport": 0},
    )
    assert weighted == pytest.approx(50.0)

    high = score_categories(
        {"safety": 1, "transport": 0},
        {"safety": 90, "transport": 10},
    )
    assert high == pytest.approx(90.0)


def test_final_score_remains_between_0_and_100():
    result = score_property(
        price=18000,
        listing_type="rent",
        property_type="apartment",
        bedrooms=2,
        area=900,
        preferences=make_preferences(),
        location_scores=LocationScores(safety=100, transport=100, healthcare=100),
        environment_scores=EnvironmentScores(environment=100, flood_risk=100),
    )
    assert 0 <= result.match_score <= 100

    poor = score_property(
        price=500000,
        listing_type="buy",
        property_type="land",
        bedrooms=0,
        area=100,
        preferences=make_preferences(),
        location_scores=LocationScores(safety=0, transport=0),
        environment_scores=EnvironmentScores(environment=0, flood_risk=0),
    )
    assert 0 <= poor.match_score <= 100
    assert poor.match_score < result.match_score


def test_recommendation_thresholds():
    assert recommendation_from_score(90) == "Excellent Match"
    assert recommendation_from_score(89.99) == "Good Match"
    assert recommendation_from_score(GOOD_MATCH_MIN) == "Good Match"
    assert recommendation_from_score(74.99) == "Moderate Match"
    assert recommendation_from_score(MODERATE_MATCH_MIN) == "Moderate Match"
    assert recommendation_from_score(59.99) == "Low Match"
    assert recommendation_from_score(EXCELLENT_MATCH_MIN) == "Excellent Match"


def test_explanation_generation():
    result = score_property(
        price=18000,
        listing_type="rent",
        property_type="apartment",
        bedrooms=2,
        area=900,
        preferences=make_preferences(),
        location_scores=LocationScores(transport=88, safety=40),
        environment_scores=EnvironmentScores(flood_risk=92, environment=30),
    )
    assert result.summary
    assert "Property fits within your preferred budget." in result.positive_factors
    assert "Property meets your minimum bedroom requirement." in result.positive_factors
    assert "Transport is a strong match." in result.positive_factors
    assert "Flood-risk conditions are favorable." in result.positive_factors
    assert any("Environment score is relatively low" in item for item in result.caution_factors)
    assert any("Safety score is relatively low" in item for item in result.caution_factors)
