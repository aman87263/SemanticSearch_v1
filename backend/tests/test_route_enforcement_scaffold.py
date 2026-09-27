from fastapi.testclient import TestClient

from app.main import app


def test_health_route_is_public_and_returns_healthy_status():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_auth_session_creation_route_is_public_and_sets_cookie():
    client = TestClient(app)

    response = client.post("/api/auth/session")

    assert response.status_code == 200
    assert response.cookies.get("semanticsearch_session")


def test_documents_route_requires_authenticated_request():
    client = TestClient(app)

    response = client.get("/api/documents")

    assert response.status_code == 401


def test_search_route_requires_authenticated_request():
    client = TestClient(app)

    response = client.post(
        "/api/search",
        json={"query": "hello", "limit": 3},
    )

    assert response.status_code == 401


def test_chat_route_requires_authenticated_request():
    client = TestClient(app)

    response = client.post(
        "/api/chat",
        json={"query": "hello", "limit": 3},
    )

    assert response.status_code == 401
