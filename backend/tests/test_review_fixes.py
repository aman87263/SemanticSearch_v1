import asyncio

import pytest

from app.services.cache import generation
from app.services.evaluation.retrieval_evaluator import (
    EvaluationQuery,
    RetrievalEvaluator,
)
from app.services.llm.llm_service import LLMService
from app.services.llm.providers.provider_router import (
    ProviderResiliencePolicy,
    ProviderRouter,
)


class AtomicRedis:
    def __init__(self):
        self.value = None
        self.lock = asyncio.Lock()

    async def eval(self, _script, _key_count, _key, initial, _ttl):
        async with self.lock:
            if self.value is None:
                self.value = int(initial)
            self.value += 1
            return self.value


@pytest.mark.asyncio
async def test_generation_bumps_are_atomic_and_seed_from_config(monkeypatch):
    client = AtomicRedis()
    monkeypatch.setattr(generation, "_redis_client", client)
    monkeypatch.setattr(generation, "_generation", 7)
    monkeypatch.setattr(generation, "_initialized", True)

    bumped = await asyncio.gather(*(generation.bump_generation() for _ in range(20)))

    assert sorted(bumped) == list(range(8, 28))
    assert client.value == 27


@pytest.mark.asyncio
async def test_provider_router_uses_configured_fallback():
    class Provider:
        def __init__(self, vector=None, error=None):
            self.vector = vector
            self.error = error

        async def embed(self, _texts):
            if self.error:
                raise self.error
            return [self.vector]

    primary = Provider(error=ConnectionError("primary unavailable"))
    fallback = Provider(vector=[0.1, 0.2])
    primary_policy = ProviderResiliencePolicy(
        "primary",
        retry_attempts=1,
        failure_threshold=10,
    )
    fallback_policy = ProviderResiliencePolicy("fallback", retry_attempts=1)
    primary_policy.set_fallback(fallback_policy)
    router = ProviderRouter(
        [primary, fallback],
        [primary_policy, fallback_policy],
    )

    assert await router.embed(["query"]) == [[0.1, 0.2]]


@pytest.mark.asyncio
async def test_llm_service_uses_resilience_and_fallback():
    class Policy:
        def __init__(self):
            self.calls = 0

        async def execute(self, operation):
            self.calls += 1
            return await operation()

    class Provider:
        def __init__(self, response=None, error=None):
            self.response = response
            self.error = error

        async def generate(self, **_kwargs):
            if self.error:
                raise self.error
            return self.response

    primary_policy = Policy()
    fallback_policy = Policy()
    service = LLMService(
        Provider(error=ConnectionError("primary unavailable")),
        resilience_policy=primary_policy,
        fallback_provider=Provider(response="fallback answer"),
        fallback_resilience_policy=fallback_policy,
    )

    assert await service.generate("question", "context") == "fallback answer"
    assert primary_policy.calls == 1
    assert fallback_policy.calls == 1


def test_ground_truth_validator_reports_unindexed_or_missing_chunk_labels():
    evaluator = RetrievalEvaluator()
    evaluator.add_query(
        EvaluationQuery(
            query="valid",
            relevant_chunk_ids=["chunk-a"],
        )
    )
    evaluator.add_query(
        EvaluationQuery(
            query="missing",
            relevant_chunk_ids=["chunk-b"],
        )
    )
    evaluator.add_query(EvaluationQuery(query="unlabeled"))

    issues = evaluator.ground_truth_issues({"chunk-a"})

    assert issues == [
        {
            "query": "missing",
            "reason": "chunk_labels_not_indexed",
            "missing_count": 1,
        },
        {"query": "unlabeled", "reason": "missing_chunk_labels"},
    ]
