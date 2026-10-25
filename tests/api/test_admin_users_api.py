from uuid import uuid4

from fastapi.testclient import TestClient

from tests.api.conftest import auth_header


def test_admin_manages_users(client: TestClient, admin_token: str, customer_token: str) -> None:
    admin = auth_header(admin_token)
    customer = client.get("/api/v1/auth/me", headers=auth_header(customer_token)).json()
    url = f"/api/v1/admin/users/{customer['id']}"

    listing = client.get("/api/v1/admin/users", params={"role": "CUSTOMER"}, headers=admin)
    detail = client.get(url, headers=admin)
    updated = client.put(url, json={"fullName": "Khách VIP", "role": "CUSTOMER"}, headers=admin)

    assert listing.status_code == 200
    assert [user["id"] for user in listing.json()["items"]] == [customer["id"]]
    assert "passwordHash" not in detail.json()
    assert detail.json() == customer
    assert updated.json()["fullName"] == "Khách VIP"
    with_email = {"fullName": "X", "role": "CUSTOMER", "email": "x@example.test"}
    assert client.put(url, json=with_email, headers=admin).status_code == 400
    assert client.delete(url, headers=admin).status_code == 204
    assert client.get(url, headers=admin).status_code == 404
    assert client.get(f"/api/v1/admin/users/{uuid4()}", headers=admin).status_code == 404


def test_only_admin_manages_users(client: TestClient, customer_token: str) -> None:
    customer = auth_header(customer_token)

    assert client.get("/api/v1/admin/users", headers=customer).status_code == 403
    assert client.get("/api/v1/admin/users").status_code == 401


def test_admin_cannot_remove_own_access(client: TestClient, admin_token: str) -> None:
    admin = auth_header(admin_token)
    me = client.get("/api/v1/auth/me", headers=admin).json()
    url = f"/api/v1/admin/users/{me['id']}"

    demoted = client.put(url, json={"fullName": "Admin", "role": "CUSTOMER"}, headers=admin)

    assert demoted.status_code == 400
    assert client.delete(url, headers=admin).status_code == 400
