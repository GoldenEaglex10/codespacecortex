"""
Core search function. Called either directly (in-process) or over
HTTP via api.py, depending on how the consuming service is deployed.

This is intentionally a thin wrapper: embed the query, hit the
tenant-scoped vector store, return typed results. The actual logic
(tenant filtering, ranking) lives in VectorStore — this function's
job is enforcing the contract.
"""

from schemas.models import SearchQuery, SearchResponse, SearchResult
from pipeline.embedder_base import Embedder
from storage.vector_store import VectorStore


def search(query: SearchQuery, embedder: Embedder, store: VectorStore) -> SearchResponse:
    if not query.tenant_id:
        # Redundant with VectorStore.search()'s own check, but fails
        # before the embedding call rather than after.
        raise ValueError("SearchQuery.tenant_id is required")

    query_embedding = embedder.embed([query.query_text])[0]

    results: list[SearchResult] = store.search(
        tenant_id=query.tenant_id,
        query_embedding=query_embedding,
        top_k=query.top_k,
    )

    return SearchResponse(
        results=results,
        tenant_id=query.tenant_id,
        query_text=query.query_text,
    )
