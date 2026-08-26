from app.services.llm.interfaces.i_llm_provider import ILLMProvider
from app.services.llm.providers.ollama_provider import OllamaProvider
from app.services.llm.providers.openai_provider import OpenAIProvider


class LLMFactory:
    @staticmethod
    def create(
        provider_name: str,
        model_name: str,
        temperature: float = 0.2,
        max_tokens: int = 1000,
    ) -> ILLMProvider:
        if provider_name == "ollama":
            return OllamaProvider(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        if provider_name == "openai":
            return OpenAIProvider(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        if provider_name == "groq":
            return OpenAIProvider(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                base_url="https://api.groq.com/openai/v1",
                api_key_environment_variable="GROQ_API_KEY",
                provider_label="Groq",
            )

        raise ValueError(f"Unsupported LLM provider: {provider_name}")
