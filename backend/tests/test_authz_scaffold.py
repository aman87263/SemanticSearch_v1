import jwt
from fastapi.testclient import TestClient

from app.main import app


def make_token(user_id: str, roles: list[str]) -> str:
    claims = {
        "sub": user_id,
        "preferred_username": user_id,
        "realm_access": {
            "roles": roles,
        },
    }
    return jwt.encode(claims, key="", algorithm="none")


def test_auth_me_returns_current_user_scaffold():
    client = TestClient(app)
    token = make_token("user-123", ["USER"])

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
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
    assert payload["data"]["realm"] == "semanticsearch"


def test_auth_me_rejects_non_demo_bearer_token_without_verifiable_user_context():
    client = TestClient(app)

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer forged-token",
        },
    )

    assert response.status_code == 401


def test_session_cookie_and_refresh_session_contract_round_trip():
    client = TestClient(app)

    create_response = client.post("/api/auth/session")
    assert create_response.status_code == 200
    payload = create_response.json()
    assert payload["success"] is True
    assert "session_id" in payload["data"]

    refresh_response = client.post("/api/auth/refresh")
    assert refresh_response.status_code == 200
    payload = refresh_response.json()
    assert payload["success"] is True
    assert payload["data"]["authenticated"] is True
    assert payload["data"]["provider"] == "keycloak"


def test_session_cookie_check_route_returns_server_session_state():
    client = TestClient(app)

    create_response = client.post("/api/auth/session")
    assert create_response.status_code == 200

    check_response = client.get("/api/auth/session")
    assert check_response.status_code == 200
    payload = check_response.json()
    assert payload["success"] is True
    assert payload["data"]["authenticated"] is True
    assert payload["data"]["provider"] == "keycloak"


def test_admin_scope_route_requires_admin_role():
    client = TestClient(app)
    token = make_token("admin-123", ["ADMIN"])

    response = client.get(
        "/api/admin/users",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["mode"] == "admin"
