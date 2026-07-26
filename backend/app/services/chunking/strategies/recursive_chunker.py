

from uuid import UUID

from app.services.chunking.strategies.i_chunking_strategy import IChunkingStrategy
from app.schemas.chunk.entities.chunk import Chunk


class RecursiveChunkingStrategy(IChunkingStrategy):
     def chunk(self, document_id: UUID, text: str) -> list[Chunk]:
         # Implement the recursive chunking logic here
         # This is a placeholder implementation
         chunks = []
         # Example logic: Split the text into sentences and create chunks
         sentences = text.split('.')
         for i, sentence in enumerate(sentences):
             if sentence.strip():  # Avoid empty sentences
                 chunk = Chunk(
                     id=UUID(int=i),  # Placeholder for unique ID generation
                     document_id=document_id,
                     content=sentence.strip()
                 )
                 chunks.append(chunk)
         return chunks