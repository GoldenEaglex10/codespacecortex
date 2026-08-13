"""
In-memory vector store, standing in for a pgvector-backed store per
the target architecture (tenant-scoped RAG over pgvector).

Implemented as a Python list with cosine similarity scoring, allowing
pipeline mechanics to be developed and tested without a Postgres
dependency. The public interface is stable so a pgvector-backed
implementation can be substituted without changes to callers.

Isolation invariant: search() requires tenant_id and filters by
tenant before scoring. Similarity is never computed across tenants
and filtered afterward — that ordering is what prevents cross-tenant
data exposure in results.
"""

import math
from schemas.models import EmbeddedChunk, SearchResult


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorStore:
    def __init__(self):
        self._chunks: list[EmbeddedChunk] = []

    def add(self, chunks: list[EmbeddedChunk]) -> None:
        for chunk in chunks:
            if not chunk.tenant_id:
                raise ValueError(f"Refusing to store chunk {chunk.chunk_id} with no tenant_id")
        self._chunks.extend(chunks)

    def count(self, tenant_id: str | None = None) -> int:
        if tenant_id is None:
            return len(self._chunks)
        return sum(1 for c in self._chunks if c.tenant_id == tenant_id)

    def search(
        self,
        tenant_id: str,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[SearchResult]:
        if not tenant_id:
            raise ValueError("tenant_id is required — cross-tenant search is not permitted")

        # Filter by tenant before scoring.
        candidates = [c for c in self._chunks if c.tenant_id == tenant_id]

        scored = [
            (chunk, _cosine_similarity(query_embedding, chunk.embedding))
            for chunk in candidates
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)

        return [
            SearchResult(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                score=round(score, 4),
                lesson_title=chunk.lesson_title,
                course_name=chunk.course_name,
                source_url=chunk.source_url,
            )
            for chunk, score in scored[:top_k]
        ]
