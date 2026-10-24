"""Integration tests for query expansion in the retrieval pipeline (§14).

These use in-memory fakes for the vector store and BM25 so they run without a
database, but they exercise the real RetrievalService wiring: expansion →
per-variant retrieval → dedupe → RRF fusion → final result.
"""

from uuid import UUID

import pytest

from app.schemas.retrieval.retrieved_chunk import RetrievedChunk
from app.services.cache.search_cache import SearchCache
from app.services.retrieval.query_rewriter import QueryRewriter
from app.services.retrieval.retrieval_service import RetrievalService


def _chunk(chunk_id: str, index: int, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        id=UUID(chunk_id),
        document_id=UUID("11111111-1111-1111-1111-111111111111"),
        index=index,
        text=f"chunk {index}",
        token_count=10,
        similarity=score,
    )


class FakeBM25:
    """Returns different chunks per query, keyed by a substring match."""

    def __init__(self, mapping: dict[str, list[RetrievedChunk]]):
        self._mapping = mapping
        self.queries: list[str] = []

    async def search(self, query, limit=5, document_id=None, user_id=None, is_admin=False):
        self.queries.append(query)
        for key, chunks in self._mapping.items():
            if key in query:
                return chunks[:limit]
        return []


class FakeVector:
    def __init__(self):
        self.queries: list[str] = []

    async def search(self, query, limit=5, document_id=None, user_id=None, is_admin=False):
        self.queries.append(query)
        return []


class FakeExpander:
    """Deterministic stand-in for an LLM provider."""

    def __init__(self, variants: str):
        self._variants = variants
        self.calls = 0

    async def generate(self, prompt, context=""):
        self.calls += 1
        return self._variants


CHUNK_A = "aaaaaaaa-0000-0000-0000-000000000001"
CHUNK_B = "bbbbbbbb-0000-0000-0000-000000000002"


class TestQueryExpansionIntegration:
    @pytest.mark.asyncio
    async def test_expansion_surfaces_extra_chunks(self):
        """The canonical query finds A; an expanded variant finds B."""
        bm25 = FakeBM25({
            "why does login fail with sso": [_chunk(CHUNK_A, 0, 1.0)],
            "single sign-on": [_chunk(CHUNK_B, 1, 1.0)],
        })

        svc = RetrievalService(
            vector_search=FakeVector(),
            bm25_search=bm25,
            reranker_service=None,
            cache=SearchCache(enabled=False),
            query_rewriter=QueryRewriter(
                llm_provider=FakeExpander("single sign-on login not working"),
                enabled=True,
            ),
        )

        results = await svc.retrieve("Why does login fail with SSO?", limit=10)
        ids = {r.id for r in results}

        assert UUID(CHUNK_A) in ids, "canonical chunk should be present"
        assert UUID(CHUNK_B) in ids, "expanded-variant chunk should be present"

    @pytest.mark.asyncio
    async def test_no_expansion_returns_only_canonical_chunk(self):
        bm25 = FakeBM25({
            "why does login fail with sso": [_chunk(CHUNK_A, 0, 1.0)],
            "single sign-on": [_chunk(CHUNK_B, 1, 1.0)],
        })

        svc = RetrievalService(
            vector_search=FakeVector(),
            bm25_search=bm25,
            reranker_service=None,
            cache=SearchCache(enabled=False),
            query_rewriter=QueryRewriter(
                llm_provider=FakeExpander("single sign-on login not working"),
                enabled=False,
            ),
        )

        results = await svc.retrieve("Why does login fail with SSO?", limit=10)
        ids = {r.id for r in results}

        assert UUID(CHUNK_A) in ids
        assert UUID(CHUNK_B) not in ids

    @pytest.mark.asyncio
    async def test_simple_query_skips_llm(self):
        """A simple query must not trigger an LLM call (§14)."""
        expander = FakeExpander("should not be used")
        bm25 = FakeBM25({"password": [_chunk(CHUNK_A, 0, 1.0)]})

        svc = RetrievalService(
            vector_search=FakeVector(),
            bm25_search=bm25,
            reranker_service=None,
            cache=SearchCache(enabled=False),
            query_rewriter=QueryRewriter(llm_provider=expander, enabled=True),
        )

        await svc.retrieve("password", limit=10)
        assert expander.calls == 0

    @pytest.mark.asyncio
    async def test_duplicate_chunks_across_variants_not_doubled(self):
        """A chunk matched by several variants must appear only once."""
        bm25 = FakeBM25({
            "why does login fail": [_chunk(CHUNK_A, 0, 1.0)],
            "login": [_chunk(CHUNK_A, 0, 0.8)],
        })

        svc = RetrievalService(
            vector_search=FakeVector(),
            bm25_search=bm25,
            reranker_service=None,
            cache=SearchCache(enabled=False),
            query_rewriter=QueryRewriter(
                llm_provider=FakeExpander("login failure"),
                enabled=True,
            ),
        )

        results = await svc.retrieve("Why does login fail with SSO?", limit=10)
        ids = [r.id for r in results]
        assert ids.count(UUID(CHUNK_A)) == 1, f"chunk duplicated: {ids}"

    @pytest.mark.asyncio
    async def test_llm_failure_does_not_break_search(self):
        """If the LLM is down, search must still work on the canonical query."""

        class BrokenLLM:
            async def generate(self, prompt, context=""):
                raise RuntimeError("LLM down")

        bm25 = FakeBM25({"why does login fail with sso": [_chunk(CHUNK_A, 0, 1.0)]})

        svc = RetrievalService(
            vector_search=FakeVector(),
            bm25_search=bm25,
            reranker_service=None,
            cache=SearchCache(enabled=False),
            query_rewriter=QueryRewriter(llm_provider=BrokenLLM(), enabled=True),
        )

        results = await svc.retrieve("Why does login fail with SSO?", limit=10)
        assert any(r.id == UUID(CHUNK_A) for r in results)

    @pytest.mark.asyncio
    async def test_all_variants_are_searched(self):
        """Each expanded variant should be issued to the retrievers."""
        bm25 = FakeBM25({
            "why does login fail with sso": [_chunk(CHUNK_A, 0, 1.0)],
            "sso error": [_chunk(CHUNK_B, 1, 1.0)],
        })

        svc = RetrievalService(
            vector_search=FakeVector(),
            bm25_search=bm25,
            reranker_service=None,
            cache=SearchCache(enabled=False),
            query_rewriter=QueryRewriter(
                llm_provider=FakeExpander("sso error"),
                enabled=True,
            ),
        )

        await svc.retrieve("Why does login fail with SSO?", limit=10)

        # Both the canonical query and the expanded variant should have run
        assert "why does login fail with sso" in bm25.queries
        assert "sso error" in bm25.queries
