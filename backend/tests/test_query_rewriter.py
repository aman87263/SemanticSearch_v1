"""Tests for LLM query rewriting/expansion (semanticAdditions.md §14)."""

import pytest

from app.services.retrieval.query_rewriter import (
    QueryRewriter,
    SimpleLLMForRewriting,
    _is_complex_query,
)


class TestComplexityGate:
    """The gate decides which queries are worth an LLM call (§14)."""

    def test_simple_single_word_not_complex(self):
        assert _is_complex_query("password") is False

    def test_simple_two_words_not_complex(self):
        assert _is_complex_query("reset password") is False

    def test_short_phrase_not_complex(self):
        assert _is_complex_query("CORS config") is False

    def test_question_word_with_many_words_is_complex(self):
        assert _is_complex_query("Why does login fail with SSO?") is True

    def test_long_query_is_complex(self):
        assert _is_complex_query("how to configure the CORS middleware in FastAPI") is True

    def test_question_mark_is_complex(self):
        assert _is_complex_query("login failing?") is True

    def test_conjunction_is_complex(self):
        assert _is_complex_query("tokens and sessions") is True


class TestQueryRewriter:
    @pytest.mark.asyncio
    async def test_simple_query_returns_canonical_only(self):
        """Simple queries skip the LLM entirely (§14: avoid blind rewriting)."""
        rewriter = QueryRewriter(enabled=True)
        variants = await rewriter.expand("password")
        assert variants == ["password"]

    @pytest.mark.asyncio
    async def test_simple_query_no_llm_call(self):
        """The LLM provider must NOT be invoked for a simple query."""

        class CountingLLM:
            def __init__(self):
                self.calls = 0

            async def generate(self, prompt, context=""):
                self.calls += 1
                return "should not be called"

        llm = CountingLLM()
        rewriter = QueryRewriter(llm_provider=llm, enabled=True)
        await rewriter.expand("password")
        assert llm.calls == 0

    @pytest.mark.asyncio
    async def test_complex_query_triggers_llm(self):
        """Complex queries should invoke the LLM exactly once."""

        class CountingLLM:
            def __init__(self):
                self.calls = 0

            async def generate(self, prompt, context=""):
                self.calls += 1
                return "login failure\nSSO error\nsingle sign-on issue"

        llm = CountingLLM()
        rewriter = QueryRewriter(llm_provider=llm, enabled=True)
        variants = await rewriter.expand("Why does login fail with SSO?")

        assert llm.calls == 1
        assert variants[0] == "why does login fail with sso"  # canonical first
        assert len(variants) > 1

    @pytest.mark.asyncio
    async def test_variants_are_canonicalized(self):
        """Every variant must be normalized so cache keys stay stable."""
        rewriter = QueryRewriter(enabled=True)
        variants = await rewriter.expand("Why does login fail with SSO?")
        for v in variants:
            assert v == v.lower()
            assert v == v.strip()

    @pytest.mark.asyncio
    async def test_max_variants_respected(self):
        class ManyVariantsLLM:
            async def generate(self, prompt, context=""):
                return "\n".join(f"variant {i}" for i in range(20))

        rewriter = QueryRewriter(
            llm_provider=ManyVariantsLLM(), enabled=True, max_variants=3
        )
        variants = await rewriter.expand("Why does login fail with SSO?")
        assert len(variants) <= 3

    @pytest.mark.asyncio
    async def test_disabled_rewriter_returns_canonical_only(self):
        rewriter = QueryRewriter(enabled=False)
        variants = await rewriter.expand("Why does login fail with SSO?")
        assert variants == ["why does login fail with sso"]

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty(self):
        rewriter = QueryRewriter(enabled=True)
        assert await rewriter.expand("") == []
        assert await rewriter.expand("   ") == []

    @pytest.mark.asyncio
    async def test_llm_failure_falls_back_to_canonical(self):
        """If the LLM raises, the rewriter must degrade gracefully (§9)."""

        class BrokenLLM:
            async def generate(self, prompt, context=""):
                raise RuntimeError("LLM unavailable")

        rewriter = QueryRewriter(llm_provider=BrokenLLM(), enabled=True)
        variants = await rewriter.expand("Why does login fail with SSO?")
        assert variants == ["why does login fail with sso"]

    @pytest.mark.asyncio
    async def test_deduplicates_identical_variants(self):
        class DupLLM:
            async def generate(self, prompt, context=""):
                return "login failure\nlogin failure\nlogin failure"

        rewriter = QueryRewriter(llm_provider=DupLLM(), enabled=True)
        variants = await rewriter.expand("Why does login fail with SSO?")
        # canonical + one deduped variant
        assert variants == ["why does login fail with sso", "login failure"]


class TestSimpleLLMFallback:
    @pytest.mark.asyncio
    async def test_fallback_produces_variants(self):
        llm = SimpleLLMForRewriting()
        from app.services.retrieval.query_rewriter import _EXPANSION_PROMPT_TEMPLATE

        prompt = _EXPANSION_PROMPT_TEMPLATE.format(query="login and authentication failure")
        result = await llm.generate(prompt)
        assert result  # non-empty
        assert "login" in result.lower()

    @pytest.mark.asyncio
    async def test_fallback_handles_no_match_prompt(self):
        llm = SimpleLLMForRewriting()
        # Prompt with no extractable query should not crash
        result = await llm.generate("garbage prompt with no query field")
        assert isinstance(result, str)
