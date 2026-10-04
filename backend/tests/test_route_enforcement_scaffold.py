from app.dependencies.questionanswer import get_question_answer_service
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.retrieval.retrieval_context import RetrievalContext
from app.services.question_answering.question_answering_service import QAResponse


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


def test_chat_route_allows_anonymous_access_to_public_documents(monkeypatch):
    client = TestClient(app)

    class StubQuestionAnswerService:
        user_id = "not-called"

        async def answer(self, **kwargs):
            self.user_id = kwargs["user_id"]
            return QAResponse(
                answer="Public document answer",
                context=RetrievalContext(items=[], text=""),
            )

    service = StubQuestionAnswerService()
    monkeypatch.setitem(
        app.dependency_overrides,
        get_question_answer_service,
        lambda: service,
    )

    response = client.post(
        "/api/chat",
        json={"query": "hello", "limit": 3},
    )

    assert response.status_code == 200
    assert service.user_id is None
