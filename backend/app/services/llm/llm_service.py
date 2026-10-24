import logging

from app.services.llm.interfaces.i_llm_provider import ILLMProvider
from app.services.resilience.circuit_breaker import ResiliencePolicy
from app.services.resilience.factory import create_llm_resilience_policy

logger = logging.getLogger(__name__)


class LLMService:

    def __init__(
        self,
        provider: ILLMProvider,
        resilience_policy: ResiliencePolicy | None = None,
        fallback_provider: ILLMProvider | None = None,
        fallback_resilience_policy: ResiliencePolicy | None = None,
    ):
        self._provider = provider
        self._resilience = resilience_policy or create_llm_resilience_policy()
        self._fallback_provider = fallback_provider
        self._fallback_resilience = (
            fallback_resilience_policy or create_llm_resilience_policy()
        )

    async def generate(
        self,
        query: str,
        context: str,
    ) -> str:

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if not context.strip():
            raise ValueError("Context cannot be empty.")

        primary_call = lambda: self._provider.generate(query=query, context=context)
        try:
            return await self._resilience.execute(primary_call)
        except Exception:
            if self._fallback_provider is None:
                raise

            logger.exception("Primary LLM provider failed; trying configured fallback")
            return await self._fallback_resilience.execute(
                lambda: self._fallback_provider.generate(query=query, context=context)
            )
