from abc import ABC, abstractmethod


class ILLMProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        query: str,
        context: str,
    ) -> str: ...
