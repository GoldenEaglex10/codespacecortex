# Search API — Integration Contract

This document specifies the interface for consumers of the knowledge
search service. Implementation details of content ingestion, chunking,
and embedding are internal and not part of this contract.

## Endpoint

```
POST /search
Content-Type: application/json
```

## Request

```json
{
  "tenant_id": "harare-high-01",
  "query_text": "how do while loops work",
  "top_k": 3
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `tenant_id` | string | Yes | Identifies the requesting institution. Must be resolved from the authenticated session/gateway, not accepted as client input. |
| `query_text` | string | Yes | The search query. |
| `top_k` | integer | No (default 5) | Maximum number of results to return. |

A request without `tenant_id` is rejected with a 4xx response. There is no unscoped search.

## Authentication

If the `SEARCH_API_KEY` environment variable is set on the server,
requests must include a matching `X-API-Key` header or they are
rejected with a 401. If unset, no key is required — intended for
local development only.

This is a minimal safeguard, not the production authentication
model. In production, this service should sit behind an internal
gateway that authenticates the caller and resolves `tenant_id` from
the caller's own session — never from client-supplied request data.

## Response

```json
{
  "results": [
    {
      "chunk_id": "cs101-l04::0",
      "text": "A loop lets you repeat a block of code multiple times...",
      "score": 0.159,
      "lesson_title": "Loops",
      "course_name": "Introduction to Programming",
      "source_url": "https://codespace.example.com/courses/cs101/lessons/4"
    }
  ],
  "tenant_id": "harare-high-01",
  "query_text": "how do while loops work"
}
```

| Field | Notes |
|---|---|
| `results` | Ordered by relevance, descending. An empty list is a valid response indicating no relevant content was found. |
| `results[].score` | Cosine similarity, typically in the 0–1 range. No minimum-relevance threshold is currently applied — see below. |
| `results[].source_url` | May be `null` (e.g. internal notes without a public link). Consumers should handle this case. |

## Known limitation: no relevance threshold

The endpoint returns its top `top_k` matches regardless of absolute
relevance. A query unrelated to any indexed content for a given
tenant will still return results, with low scores.

Consumers should not treat a non-empty `results` list as confirmation
of relevance. Recommended handling: apply a minimum score threshold
before using a result, or instruct the downstream model that
low-scoring results may be irrelevant and should not be cited as
authoritative.

Threshold calibration is pending and depends on evaluation against a
production embedding model.

## Current implementation status

The endpoint is functional and the request/response contract is
stable. It is currently backed by:
- Fixture-based content (not yet connected to a production content source)
- A placeholder embedder based on lexical similarity, not a trained semantic model

Result quality will improve as these are replaced with production
components; the contract above will not change as a result.

## Running locally

```bash
cd knowledge-pipeline
pip install -r requirements.txt
uvicorn pipeline.api:app --reload --port 8000
```

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "harare-high-01", "query_text": "how do while loops work", "top_k": 3}'
```

`GET /health` returns `{"status": "ok", "chunks_indexed": <n>}` and can be used to verify the service is running and indexed.
