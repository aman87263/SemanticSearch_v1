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


def test_admin_audit_route_scaffold_returns_audit_events_list():
    client = TestClient(app)

    response = client.get(
        "/api/admin/audit",
        headers={
            "Authorization": f"Bearer {make_token('admin-123', ['ADMIN'])}",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert isinstance(payload["data"]["audit_events"], list)
