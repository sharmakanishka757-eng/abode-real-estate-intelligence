"""Smoke tests for Milestone 1 property CRUD."""

from tests.conftest import create_sample_property


def test_create_and_get_property(client):
    created = create_sample_property(client, title="CRUD apartment")
    response = client.get(f"/properties/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "CRUD apartment"


def test_list_properties(client):
    create_sample_property(client, title="One")
    create_sample_property(client, title="Two", price=21000)
    response = client.get("/properties")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_update_and_delete_property(client):
    created = create_sample_property(client)
    updated = client.put(f"/properties/{created['id']}", json={"price": 22000})
    assert updated.status_code == 200
    assert float(updated.json()["price"]) == 22000

    deleted = client.delete(f"/properties/{created['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/properties/{created['id']}").status_code == 404
    assert client.get("/properties/9999").status_code == 404
