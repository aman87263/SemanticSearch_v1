from dataclasses import dataclass
from uuid import UUID

from app.services.context.context_builder_service import (
    ContextBuilderService,
)
from app.services.retrieval.retrieval_service import RetrievalService
from app.schemas.retrieval.retrieval_context import RetrievalContext
from app.services.llm.llm_service import LLMService


@dataclass(frozen=True)
class QAResponse:
    answer: str
    context: RetrievalContext


class QuestionAnsweringService:

    def __init__(
        self,
        retrieval_service: RetrievalService,
        context_builder: ContextBuilderService,
        llm_service: LLMService,
        default_max_chars: int = 8000,
    ):
        self._retrieval_service = retrieval_service
        self._context_builder = context_builder
        self._llm_service = llm_service
        self._default_max_chars = default_max_chars

    async def answer(
        self,
        query: str,
        limit: int = 5,
        document_id: UUID | None = None,
        max_chars: int | None = None,
    ) -> QAResponse:

        chunks = await self._retrieval_service.retrieve(
            query=query,
            limit=limit,
            document_id=document_id,
        )

        context = self._context_builder.build(
            chunks=chunks,
            max_chars=(self._default_max_chars if max_chars is None else max_chars),
        )

        generated_answer = await self._llm_service.generate(
            query=query,
            context=context.text,
        )

        return QAResponse(
            answer=generated_answer,
            context=context,
        )
