from typing import Annotated

from fastapi import Depends

from app.core.settings import settings
from app.dependencies.retrieval import get_retrieval_service
from app.services.context.context_builder_service import ContextBuilderService
from app.services.llm.interfaces.i_llm_provider import ILLMProvider
from app.services.llm.providers.llm_factory import LLMFactory
from app.services.question_answering.question_answering_service import (
    QuestionAnsweringService,
)
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.llm.llm_service import LLMService


def get_llm_provider() -> ILLMProvider:
    return LLMFactory.create(
        provider_name=settings.llm.provider,
        model_name=settings.llm.model,
        temperature=settings.llm.temperature,
        max_tokens=settings.llm.max_tokens,
    )


def get_llm_service(
    provider: Annotated[
        ILLMProvider,
        Depends(get_llm_provider),
    ],
) -> LLMService:

    return LLMService(provider)


def get_question_answer_service(
    retrieval_service: Annotated[
        RetrievalService,
        Depends(get_retrieval_service),
    ],
    llm_service: Annotated[
        LLMService,
        Depends(get_llm_service),
    ],
) -> QuestionAnsweringService:
    return QuestionAnsweringService(
        retrieval_service=retrieval_service,
        context_builder=ContextBuilderService(),
        llm_service=llm_service,
    )
