from app.schemas.chat.citation import Citation
from app.schemas.retrieval.retrieval_context import ContextItem


class CitationService:
    def create(self, items: list[ContextItem]) -> list[Citation]:
        return [
            Citation(
                document_id=item.document_id,
                document_name=item.document_name,
                chunk_id=item.chunk_id,
                chunk_index=item.chunk_index,
                similarity=item.score,
                rerank_score=item.rerank_score,
            )
            for item in items
        ]