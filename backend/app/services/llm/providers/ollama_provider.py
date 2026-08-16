import asyncio
import json
import os
from urllib import error, request

from app.services.llm.interfaces.i_llm_provider import ILLMProvider


class OllamaProvider(ILLMProvider):
    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1000,
    ):
        self._model = model
        self._base_url = (base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")
        self._temperature = temperature
        self._max_tokens = max_tokens

    def _build_prompt(self, query: str, context: str) -> str:
        return (
            "Use the provided context to answer the user's question. "
            "If the answer is not in the context, say so clearly.\n\n"
            f"Question: {query}\n\nContext:\n{context}"
        )

    def _generate_sync(self, query: str, context: str) -> str:
        payload = {
            "model": self._model,
            "prompt": self._build_prompt(query, context),
            "stream": False,
            "options": {
                "temperature": self._temperature,
                "num_predict": self._max_tokens,
            },
        }

        req = request.Request(
            f"{self._base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=180) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(
                f"Ollama is not reachable at {self._base_url}. "
                "Start it with 'ollama serve' or set OLLAMA_BASE_URL."
            ) from exc

        if not isinstance(body, dict):
            raise RuntimeError("Unexpected response format from Ollama.")

        answer = body.get("response")
        return str(answer).strip() if answer is not None else ""

    async def generate(self, query: str, context: str) -> str:
        return await asyncio.to_thread(self._generate_sync, query, context)
