from app.schemas.retrieval.retrieval_context import ContextItem, RetrievalContext
from app.schemas.retrieval.retrieved_chunk import RetrievedChunk


class ContextBuilderService:

    def build(
        self,
        chunks: list[RetrievedChunk],
        max_chars: int | None = None,
    ) -> RetrievalContext:

        if not chunks:
            return RetrievalContext(
                items=[],
                text="",
            )

        ordered_chunks = sorted(
            chunks,
            key=lambda chunk: (
                str(chunk.document_id),
                chunk.index,
            ),
        )

        items: list[ContextItem] = []
        formatted_sections: list[str] = []
        current_length = 0

        for chunk in ordered_chunks:

            item = ContextItem(
                document_id=chunk.document_id,
                chunk_id=chunk.id,
                chunk_index=chunk.index,
                text=chunk.text,
                score=chunk.similarity,
                rerank_score=chunk.rerank_score,
            )

            section = (
                f'<document id="{item.document_id}" '
                f'index="{item.chunk_index}">\n'
                f"{item.text}\n"
                f"</document>"
            )

            if max_chars is not None and (current_length + len(section)) > max_chars:
                continue

            items.append(item)
            formatted_sections.append(section)
            current_length += len(section)

        return RetrievalContext(
            items=items,
            text="\n\n".join(formatted_sections),
        )
