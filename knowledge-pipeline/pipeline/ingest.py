"""
Ingestion pipeline: fetches content from a connector, chunks it,
generates embeddings, and stores the result.

Currently configured with fixture-backed components. Switching to
production components requires changing only build_default_pipeline()
below — no other pipeline module needs modification.
"""

from connector.fake_connector import FakeConnector
from pipeline.chunker import chunk_content_item
from pipeline.fake_embedder import FakeEmbedder
from storage.vector_store import VectorStore
from schemas.models import EmbeddedChunk


def ingest(connector, embedder, store: VectorStore, tenant_id: str | None = None) -> int:
    """
    Runs the full pipeline: fetch -> chunk -> embed -> store.
    Returns the number of chunks ingested.
    """
    raw_items = connector.fetch_all(tenant_id=tenant_id)

    all_chunks = []
    for item in raw_items:
        all_chunks.extend(chunk_content_item(item))

    if not all_chunks:
        return 0

    texts = [c.text for c in all_chunks]
    embeddings = embedder.embed(texts)

    embedded_chunks = [
        EmbeddedChunk(**chunk.model_dump(), embedding=embedding)
        for chunk, embedding in zip(all_chunks, embeddings)
    ]

    store.add(embedded_chunks)
    return len(embedded_chunks)


def build_default_pipeline() -> tuple:
    """
    Constructs the pipeline components currently in use.

    To switch to production components, replace the two lines below:
        connector = CodespaceConnector(api_key=...)
        embedder = RealEmbedder(model_name=..., dimensions=...)
    """
    connector = FakeConnector()
    embedder = FakeEmbedder()
    store = VectorStore()
    return connector, embedder, store


if __name__ == "__main__":
    connector, embedder, store = build_default_pipeline()
    n = ingest(connector, embedder, store)
    print(f"Ingested {n} chunks into the vector store.")
    print(f"  harare-high-01: {store.count('harare-high-01')} chunks")
    print(f"  bulawayo-college-02: {store.count('bulawayo-college-02')} chunks")
    print(f"  total: {store.count()} chunks")
