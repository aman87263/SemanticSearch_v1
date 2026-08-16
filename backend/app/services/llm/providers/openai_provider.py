import asyncio
import json
import os
from urllib import request

from app.services.llm.interfaces.i_llm_provider import ILLMProvider


class OpenAIProvider(ILLMProvider):
    def __init__(
        self,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1000,
        base_url: str = "https://api.openai.com/v1",
    ):
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._base_url = base_url.rstrip("/")
        self._api_key = os.getenv("OPENAI_API_KEY")

    def _build_prompt(self, query: str, context: str) -> str:
        return (
            "Use the provided context to answer the user's question. "
            "If the answer is not in the context, say so clearly.\n\n"
            f"Question: {query}\n\nContext:\n{context}"
        )

    def _generate_sync(self, query: str, context: str) -> str:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        payload = {
            "model": self._model,
            "messages": [
                {"role": "user", "content": self._build_prompt(query, context)}
            ],
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }

        req = request.Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )

        with request.urlopen(req, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))

        choices = body.get("choices") or []
        if not choices:
            raise RuntimeError("OpenAI returned no choices.")

        message = choices[0].get("message", {}).get("content", "")
        return str(message).strip()

    async def generate(self, query: str, context: str) -> str:
        return await asyncio.to_thread(self._generate_sync, query, context)
