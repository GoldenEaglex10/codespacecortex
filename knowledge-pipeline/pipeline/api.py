"""
Search API — exposes the knowledge pipeline's search as a REST
endpoint for downstream consumers (e.g. the tutor service).

Run with:
    uvicorn pipeline.api:app --reload --port 8000

Example request:
    POST http://localhost:8000/search
    Headers: X-API-Key: <value of SEARCH_API_KEY>
    Body: { "tenant_id": "harare-high-01", "query_text": "how do while loops work", "top_k": 3 }

On startup, this ingests fixture data so the index is populated
immediately. Swap FakeConnector/FakeEmbedder for production
implementations in pipeline/ingest.py's build_default_pipeline() —
this file does not need to change when that happens.

Authentication: this service expects to sit behind an internal
gateway that authenticates the caller and resolves tenant_id from
the caller's own session — never from client-supplied input. The
X-API-Key check below is a minimal safeguard for direct/local use
and is not a substitute for that gateway-level authentication.
"""

import os
from fastapi import FastAPI, HTTPException, Header

from schemas.models import SearchQuery, SearchResponse
from pipeline.ingest import build_default_pipeline, ingest
from pipeline.search_tool import search as run_search

app = FastAPI(title="Cortex Knowledge Search API", version="0.1.0")

SEARCH_API_KEY = os.environ.get("SEARCH_API_KEY")

# Shared pipeline instance for this process. A production deployment
# would load the store from Postgres/pgvector rather than re-ingesting
# fixture data on every startup.
_connector, _embedder, _store = build_default_pipeline()
_chunk_count = ingest(_connector, _embedder, _store)


def _check_api_key(x_api_key: str | None) -> None:
    if SEARCH_API_KEY is None:
        # No key configured (e.g. local development) — skip the check
        # rather than lock the service out of a usable default state.
        return
    if x_api_key != SEARCH_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "chunks_indexed": _store.count(),
    }


@app.post("/search", response_model=SearchResponse)
def search_endpoint(query: SearchQuery, x_api_key: str | None = Header(default=None)) -> SearchResponse:
    _check_api_key(x_api_key)

    if not query.tenant_id:
        # tenant_id is already required by the SearchQuery schema;
        # this check produces a clearer error message than the
        # default validation response.
        raise HTTPException(status_code=400, detail="tenant_id is required")

    try:
        return run_search(query, _embedder, _store)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
