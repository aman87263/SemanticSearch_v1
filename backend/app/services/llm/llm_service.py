from app.services.llm.interfaces.i_llm_provider import ILLMProvider


class LLMService:

    def __init__(self, provider: ILLMProvider):
        self._provider = provider

    async def generate(
        self,
        query: str,
        context: str,
    ) -> str:

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if not context.strip():
            raise ValueError("Context cannot be empty.")

        return await self._provider.generate(
            query=query,
            context=context,
        )
