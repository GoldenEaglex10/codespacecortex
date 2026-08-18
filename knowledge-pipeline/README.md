# Knowledge Pipeline

Ingests course content, indexes it for semantic search, and exposes
a tenant-scoped search API. This implements the Knowledge Layer and
Connector Layer of the Cortex architecture.

## Pipeline

```
Source content -> Connector -> Chunker -> Embedder -> Vector Store -> Search API
```

## Project layout

```
connector/
  base.py                  # Connector interface
  fake_connector.py        # Fixture-backed connector implementation
  codespace_connector.py   # Production connector (pending API integration)

schemas/
  models.py                # RawContentItem, Chunk, EmbeddedChunk, SearchQuery, SearchResponse

fixtures/
  sample_courses.py        # Sample content across two tenants, for isolation testing

pipeline/
  chunker.py                # Paragraph-first / sentence-fallback chunking with overlap
  embedder_base.py          # Embedder interface
  fake_embedder.py          # Placeholder embedder (lexical similarity)
  real_embedder.py          # Production embedder (pending model selection)
  ingest.py                 # Fetch -> chunk -> embed -> store pipeline
  search_tool.py            # Core search function
  api.py                    # FastAPI REST endpoint

storage/
  vector_store.py           # In-memory, tenant-scoped vector store (pgvector substitute)

tests/
  test_connector.py
  test_chunker.py
  test_search.py            # Includes tenant-isolation checks

CHUNKING.md                 # Chunking strategy documentation
HANDOFF.md                  # Search API contract for downstream consumers
```

## Setup

```bash
pip install -r requirements.txt
```

## Running

```bash
# Run tests
python3 -m tests.test_connector
python3 -m tests.test_chunker
python3 -m tests.test_search

# Start the API
uvicorn pipeline.api:app --reload --port 8000

# Example request
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "harare-high-01", "query_text": "how do while loops work", "top_k": 3}'
```

## Implementation status

| Component | Status |
|---|---|
| Connector interface | Complete |
| Production connector | Pending — requires API base URL, auth, and endpoint details |
| Chunking | Complete |
| Embedder interface | Complete |
| Placeholder embedder | Complete (lexical similarity, not semantic) |
| Production embedder | Pending — requires model/provider selection |
| Vector store | Complete (in-memory; pgvector migration pending) |
| Search API | Complete and testable |

## Integration points

The following are the only changes required to move from
fixture-backed to production components:

1. `connector/codespace_connector.py` — base URL, auth, endpoint paths
2. `pipeline/real_embedder.py` — embedding model integration
3. `pipeline/ingest.py::build_default_pipeline()` — swap connector/embedder instances
4. `storage/vector_store.py` — pgvector-backed implementation

No other module requires changes when these are integrated.

## Checklist

- [x] Connector interface and REST adapter scaffold
- [x] Typed schemas and fixture data
- [x] Chunking strategy implemented and documented
- [x] Embedding wrapper and ingestion script
- [x] Tenant-scoped vector retrieval
- [x] End-to-end ingestion verified
- [x] Search quality verified against sample queries
- [x] Search API contract documented (see HANDOFF.md)
- [ ] Full security/isolation test pass (basic coverage in `test_search.py`; broader adversarial testing pending)
