"""Query rewriting and expansion for multi-term retrieval.

Implements semanticAdditions.md §14:

  User query
      →
  Query normalization
      →
  Query rewriting / expansion
      →
  +---------------+
  | BM25          |
  | Dense         |
  +---------------+

The rewriter expands a single user query into multiple search variants so that
both the sparse (BM25) and dense retrievers receive stronger signals.

Design principles (per §14):
  - Don't blindly LLM-rewrite every query. Simple queries go straight to search.
  - Only complex/multi-term queries trigger the LLM expansion.
  - Expansion produces 2-4 variants: an LLM-generated reformulation plus
    keyword-focused variants.
  - Each variant is searched via both BM25 and dense; RRF fuses the results.
"""

import logging
import re
from typing import Protocol

from app.services.resilience.factory import create_llm_resilience_policy

logger = logging.getLogger(__name__)

# A single prompt that expands a query. We keep it lightweight so the model
# is cheap and deterministic. The result is newline-separated variants.
_EXPANSION_PROMPT_TEMPLATE = """\
You are a query expansion assistant for a technical knowledge search engine.
Given the user query, produce up to 3 alternative search queries that capture
the same intent. Each variant should be on its own line. Do NOT answer the
question — only output the alternative queries.

Examples:
  Query: "Why does login fail with SSO?" -> "login SSO failure", "SSO authentication error", "single sign-on login not working"
  Query: "How to reset password" -> "password reset instructions", "forgot password reset", "account password recovery"

Query: "{query}"
Variants:"""


class ILLMProvider(Protocol):
    """Minimal protocol for whatever LLM provider the app uses."""
    async def generate(self, query: str, context: str) -> str: ...


class SimpleLLMForRewriting:
    """Fallback rule-based expansion used in dev / when no LLM is configured.

    Returns deterministic variants so the pipeline works without an LLM
    provider and so tests remain hermetic.
    """

    async def generate(self, prompt: str, context: str = "") -> str:
        # Extract the original query from the rendered prompt
        match = re.search(r'Query: "(.+?)"\s*\nVariants:', prompt)
        query = match.group(1) if match else ""

        # Simple expansion: split on common connectors
        parts = re.split(
            r'\s+(?:and|or|what is|how to|does|do|the|to)\s+',
            query, flags=re.IGNORECASE,
        )
        variants = [query]  # always include the original
        for part in parts:
            part = part.strip().strip("?.,!")
            if part and len(part) > 2 and part != query:
                variants.append(part)
        return "\n".join(variants[:3])


def _is_complex_query(query: str) -> bool:
    """Gate: only send queries above a complexity threshold to the LLM.

    Per §14: "simple query -> direct search, complex query -> rewrite/expand."

    A query is considered complex if:
      - It contains more than 6 words, or
      - It contains question words combined with more than 3 words, or
      - It has multiple clauses ('?' or 'and'/'or')
    """
    q = query.strip()
    word_count = len(q.split())

    if word_count > 6:
        return True

    question_words = re.compile(
        r'\b(who|what|why|how|when|where|can|does|do|is|are)\b',
        re.IGNORECASE,
    )
    has_question_words = bool(question_words.search(q))

    if has_question_words and word_count > 3:
        return True

    if '?' in q or re.search(r'\b(and|or)\b', q, re.IGNORECASE):
        return True

    return False


class QueryRewriter:
    """Rewrites user queries into multiple search variants for hybrid retrieval.

    Uses a complexity gate to avoid LLM cost on trivial queries. Each variant
    is canonicalized before searching so cache keys stay stable.

    The `enabled` flag comes from configuration; when disabled the rewriter
    simply returns the single canonicalized query.
    """

    def __init__(
        self,
        llm_provider: ILLMProvider | None = None,
        enabled: bool = True,
        max_variants: int = 3,
        llm_resilience_policy=None,
        fallback_provider: ILLMProvider | None = None,
    ):
        self._llm_provider = llm_provider or SimpleLLMForRewriting()
        self._enabled = enabled
        self._max_variants = max_variants
        self._llm_resilience = llm_resilience_policy or create_llm_resilience_policy()
        self._fallback_provider = fallback_provider

    async def expand(self, raw_query: str) -> list[str]:
        """Expand a raw query into a list of search variants.

        Returns a list of query strings. The first element is always the
        original (canonicalized) query. Subsequent elements are variants.

        Args:
            raw_query: The user's original query string.

        Returns:
            List of query variants, deduplication, max ``max_variants`` total.
        """
        from app.services.retrieval.query_normalizer import normalize_query

        if not raw_query or not raw_query.strip():
            return []

        canonical = normalize_query(raw_query)
        if not canonical:
            return []

        if not self._enabled or not _is_complex_query(raw_query):
            return [canonical]

        try:
            prompt = _EXPANSION_PROMPT_TEMPLATE.format(query=raw_query)
            raw_response = await self._llm_resilience.execute(
                lambda: self._llm_provider.generate(prompt, context="")
            )

        except Exception:
            # Try fallback provider if available
            if self._fallback_provider is not None:
                try:
                    logger.warning(
                        "Primary LLM provider failed for query rewriting; "
                        "attempting configured fallback provider"
                    )
                    raw_response = await self._llm_resilience.execute(
                        lambda: self._fallback_provider.generate(prompt, context="")
                    )
                except Exception:
                    logger.exception(
                        "Query rewriting fallback also failed; "
                        "falling back to canonical query only"
                    )
                    return [canonical]
            else:
                logger.exception(
                    "Query rewriting failed; falling back to canonical query only"
                )
                return [canonical]

        # Parse newline-separated variants
        variants: list[str] = []
        for line in raw_response.strip().split("\n"):
            line = line.strip().strip("'\"-•")
            if line and line != raw_query:
                variants.append(normalize_query(line))

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_variants: list[str] = []
        for v in variants:
            if v and v not in seen:
                seen.add(v)
                unique_variants.append(v)

        # Always include the canonical version first
        all_variants = [canonical] + unique_variants[: self._max_variants - 1]

        logger.info(
            f"Query rewrite: '{raw_query[:60]}' -> "
            f"{len(all_variants)} variants"
        )
        return all_variants