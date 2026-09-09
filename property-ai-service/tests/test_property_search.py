"""Tests for GET /properties/search."""

from tests.conftest import create_sample_property


def test_search_by_city(client):
    create_sample_property(client, title="Jaipur home", city="Jaipur")
    create_sample_property(client, title="Ajmer home", city="Ajmer", address="Ajmer")

    response = client.get("/properties/search", params={"city": "jaipur"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["results"][0]["city"] == "Jaipur"


def test_search_by_listing_type(client):
    create_sample_property(client, title="For rent", listing_type="rent")
    create_sample_property(client, title="For sale", listing_type="buy", price=4000000)

    response = client.get("/properties/search", params={"listing_type": "rent"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["results"][0]["listing_type"] == "rent"


def test_search_by_property_type(client):
    create_sample_property(client, title="Apartment", property_type="apartment")
    create_sample_property(
        client,
        title="Plot",
        property_type="land",
        listing_type="buy",
        bedrooms=None,
        bathrooms=None,
        price=2000000,
    )

    response = client.get("/properties/search", params={"property_type": "land"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["results"][0]["property_type"] == "land"


def test_search_by_min_and_max_price(client):
    create_sample_property(client, title="Cheap rent", price=9000)
    create_sample_property(client, title="Mid rent", price=18000)
    create_sample_property(client, title="High rent", price=40000)

    response = client.get(
        "/properties/search",
        params={"min_price": 10000, "max_price": 25000},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["results"][0]["title"] == "Mid rent"


def test_search_by_bedroom_filters(client):
    create_sample_property(client, title="1 bed", bedrooms=1)
    create_sample_property(client, title="2 bed", bedrooms=2)
    create_sample_property(client, title="4 bed", bedrooms=4, property_type="house")

    response = client.get(
        "/properties/search",
        params={"min_bedrooms": 2, "max_bedrooms": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["results"][0]["bedrooms"] == 2


def test_search_with_multiple_filters(client):
    create_sample_property(
        client,
        title="Match",
        city="Jaipur",
        listing_type="rent",
        property_type="apartment",
        price=15000,
        bedrooms=2,
        area=880,
    )
    create_sample_property(
        client,
        title="Wrong listing",
        city="Jaipur",
        listing_type="buy",
        property_type="apartment",
        price=15000,
        bedrooms=2,
    )
    create_sample_property(
        client,
        title="Too expensive rent",
        city="Jaipur",
        listing_type="rent",
        property_type="apartment",
        price=40000,
        bedrooms=2,
    )

    response = client.get(
        "/properties/search",
        params={
            "city": "Jaipur",
            "listing_type": "rent",
            "property_type": "apartment",
            "max_price": 25000,
            "min_bedrooms": 2,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["results"][0]["title"] == "Match"


def test_search_with_no_matching_properties(client):
    create_sample_property(client, city="Jaipur")

    response = client.get("/properties/search", params={"city": "Delhi"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["results"] == []
    assert body["skip"] == 0
    assert body["limit"] == 20


def test_search_pagination(client):
    for index in range(5):
        create_sample_property(
            client,
            title=f"Jaipur listing {index}",
            city="Jaipur",
            price=10000 + index,
        )

    first_page = client.get(
        "/properties/search",
        params={"city": "Jaipur", "skip": 0, "limit": 2},
    )
    assert first_page.status_code == 200
    first_body = first_page.json()
    assert first_body["total"] == 5
    assert first_body["skip"] == 0
    assert first_body["limit"] == 2
    assert len(first_body["results"]) == 2

    second_page = client.get(
        "/properties/search",
        params={"city": "Jaipur", "skip": 2, "limit": 2},
    )
    assert second_page.status_code == 200
    second_body = second_page.json()
    assert second_body["total"] == 5
    assert len(second_body["results"]) == 2
    first_ids = {item["id"] for item in first_body["results"]}
    second_ids = {item["id"] for item in second_body["results"]}
    assert first_ids.isdisjoint(second_ids)


def test_search_invalid_query_parameters(client):
    assert client.get("/properties/search", params={"listing_type": "lease"}).status_code == 422
    assert client.get("/properties/search", params={"property_type": "villa"}).status_code == 422
    assert client.get("/properties/search", params={"min_price": -1}).status_code == 422
    assert client.get("/properties/search", params={"skip": -1}).status_code == 422
    assert client.get("/properties/search", params={"limit": 0}).status_code == 422
    assert client.get("/properties/search", params={"limit": 500}).status_code == 422
    assert client.get("/properties/search", params={"min_bedrooms": -2}).status_code == 422
