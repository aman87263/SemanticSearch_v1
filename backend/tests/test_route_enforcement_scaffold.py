from fastapi.testclient import TestClient

from app.main import app


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
