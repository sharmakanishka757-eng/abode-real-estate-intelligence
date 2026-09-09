"""API tests for preferences and property analysis."""

from tests.conftest import create_sample_property


def preference_payload(**overrides) -> dict:
    payload = {
        "user_id": "user-1",
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
        "noise_connectivity_weight": 1,
    }
    payload.update(overrides)
    return payload


def analyze_payload() -> dict:
    prefs = preference_payload()
    prefs.pop("user_id")
    return {
        "user_preferences": prefs,
        "location_scores": {
            "safety": 90,
            "transport": 85,
            "healthcare": 80,
            "education": 70,
            "amenities": 88,
            "noise_connectivity": 75,
        },
        "environment_scores": {
            "environment": 80,
            "water_utilities": 65,
            "flood_risk": 90,
        },
    }


def test_preference_crud(client):
    created = client.post("/preferences", json=preference_payload())
    assert created.status_code == 201, created.text
    assert created.json()["user_id"] == "user-1"

    duplicate = client.post("/preferences", json=preference_payload())
    assert duplicate.status_code == 409

    fetched = client.get("/preferences/user-1")
    assert fetched.status_code == 200
    assert fetched.json()["min_bedrooms"] == 2

    updated = client.put("/preferences/user-1", json={"max_budget": 30000})
    assert updated.status_code == 200
    assert float(updated.json()["max_budget"]) == 30000

    missing = client.get("/preferences/unknown")
    assert missing.status_code == 404

    deleted = client.delete("/preferences/user-1")
    assert deleted.status_code == 204
    assert client.get("/preferences/user-1").status_code == 404


def test_analyze_endpoint_with_valid_data(client):
    property_item = create_sample_property(
        client,
        title="Vaishali 2BHK",
        price=18000,
        bedrooms=2,
        area=900,
    )
    response = client.post(
        f"/properties/{property_item['id']}/analyze",
        json=analyze_payload(),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["property_id"] == property_item["id"]
    assert 0 <= body["match_score"] <= 100
    assert body["recommendation"] in {
        "Excellent Match",
        "Good Match",
        "Moderate Match",
        "Low Match",
    }
    assert body["summary"]
    assert isinstance(body["positive_factors"], list)
    assert "property" in body
    assert body["property"]["title"] == "Vaishali 2BHK"
    assert body["category_scores"]["transport"] == 85
    assert body["category_scores"]["flood_risk"] == 90


def test_analyze_endpoint_with_invalid_data(client):
    property_item = create_sample_property(client)
    invalid_weights = analyze_payload()
    for key in invalid_weights["user_preferences"]:
        if key.endswith("_weight"):
            invalid_weights["user_preferences"][key] = 0
    response = client.post(
        f"/properties/{property_item['id']}/analyze",
        json=invalid_weights,
    )
    assert response.status_code == 422

    invalid_score = analyze_payload()
    invalid_score["location_scores"]["safety"] = 150
    response = client.post(
        f"/properties/{property_item['id']}/analyze",
        json=invalid_score,
    )
    assert response.status_code == 422


def test_analyze_endpoint_with_nonexistent_property(client):
    response = client.post("/properties/9999/analyze", json=analyze_payload())
    assert response.status_code == 404
