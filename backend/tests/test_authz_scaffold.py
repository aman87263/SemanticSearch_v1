from fastapi.testclient import TestClient

from app.main import app


def test_auth_me_returns_current_user_scaffold():
    client = TestClient(app)

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer demo-token",
            "X-User-Id": "user-123",
            "X-User-Role": "USER",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["user_id"] == "user-123"
    assert payload["data"]["roles"] == ["USER"]


def test_auth_keycloak_config_scaffold_returns_provider_metadata():
    client = TestClient(app)

    response = client.get("/api/auth/keycloak/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["provider"] == "keycloak"
    assert payload["data"]["realm"] == "master"


def test_admin_scope_route_requires_admin_role():
    client = TestClient(app)

    response = client.get(
        "/api/admin/users",
        headers={
            "Authorization": "Bearer demo-token",
            "X-User-Id": "admin-123",
            "X-User-Role": "ADMIN",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["mode"] == "admin"
