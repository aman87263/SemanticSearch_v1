from fastapi.testclient import TestClient

from app.main import app


def test_admin_audit_route_scaffold_returns_audit_events_list():
    client = TestClient(app)

    response = client.get(
        "/api/admin/audit",
        headers={
            "Authorization": "Bearer demo-token",
            "X-User-Id": "admin-123",
            "X-User-Role": "ADMIN",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert isinstance(payload["data"]["audit_events"], list)
