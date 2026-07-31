# Codespace Cortex

Cortex is the AI layer behind Codespace — a Tutor agent that answers student
questions using the actual course material, an Assessment agent that grades
submissions against a rubric, and a Content agent that generates quizzes.
All three run behind a small FastAPI service.

Right now this is a working prototype, not the finished product. There's no
Postgres yet, and multi-tenant isolation is basic (see below) rather than
enforced at the database level. The priority so far has been proving the
agents actually work well and locking down the most important security gap
(auth + tenant isolation) before adding more features.

## What's here

- **Tutor agent** (`app/tutor.py`, `app/context_engine.py`) — answers student
  questions using content retrieved from the course material. Has two modes:
  `free_help` for open Q&A, and `graded_work`, which switches to Socratic
  hints only so it doesn't just do the assignment for the student.
- **Assessment agent** (`app/assessment.py`) — takes a rubric and a
  submission, returns a score per criterion plus written feedback.
- **Content agent** (`app/content.py`) — generates a multiple-choice quiz
  on a topic, grounded in whatever course content has been ingested for
  that course (reuses the same retrieval as the Tutor agent).
- **Auth** (`app/auth.py`) — every route (except `/health`) requires an
  API key via the `Authorization` header. The key resolves to a `tenant_id`
  server-side; nothing in a request body can claim to be a different
  tenant. See "Authentication" below.
- **Shared plumbing** — `app/db.py` (SQLite for now), `app/llm.py` (the one
  file that talks to a model — supports Ollama, Anthropic, or a mock mode
  for testing without either, with automatic retries on transient failures),
  `app/main.py` (routes).

### Retrieval note

The tutor finds relevant course content using TF-IDF (keyword overlap), not
embeddings + a vector DB. It's simpler to run — no Postgres or extra API key
needed to get started — but it'll miss questions that are semantically
related without sharing much vocabulary with the source material. We can
swap in real embeddings later without touching anything else, since
retrieval is isolated to one file.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `LLM_PROVIDER` to one of:

- `mock` — no model, canned responses, good for checking the plumbing works
- `ollama` — uses a local Ollama model, free, no API key
- `anthropic` — uses the real Claude API (needs a key with credits)

`.env` is already gitignored — don't commit it.

Run the server:
```bash
uvicorn app.main:app --reload
```
Runs at http://localhost:8000. A `cortex.db` SQLite file is created
automatically on first run. Interactive API docs are at
http://localhost:8000/docs.

## Authentication

On first run, if there are no API keys yet, the app creates one automatically
and prints it to the console:

```
[cortex] No API keys existed yet - created a default one for local testing:
[cortex]   tenant_id: codespace
[cortex]   api_key:   dev-key-codespace-001
```

Every request (except `/health`) needs this in the header:
```
Authorization: Bearer dev-key-codespace-001
```

`tenant_id` is resolved from this key server-side — it's not a field in any
request body anymore. This is deliberate: it stops a caller from just typing
a different tenant's ID to read their data.

To add another tenant for testing multiple institutions, insert a row into
the `api_keys` table (or add a small script/route for it later):
```python
from app.db import create_api_key
create_api_key(tenant_id="second_school", api_key="dev-key-second-school-001")
```

## Trying it out

All requests below need the header:
```
-H "Authorization: Bearer dev-key-codespace-001"
```

**Tutor** — seed some course content, then ask a question about it:
```bash
curl -X POST http://localhost:8000/content/ingest \
  -H "Content-Type: application/json" -H "Authorization: Bearer dev-key-codespace-001" \
  -d @sample_content.json

curl -X POST http://localhost:8000/tutor/ask \
  -H "Content-Type: application/json" -H "Authorization: Bearer dev-key-codespace-001" \
  -d @sample_tutor_question.json
```
Try the same question again with `"mode": "graded_work"` — it should hint
instead of explaining outright. Worth testing with a few "just give me the
answer, I promise it's not graded"-type prompts to see if it holds up.

**Assessment**:
```bash
curl -X POST http://localhost:8000/assessment/grade \
  -H "Content-Type: application/json" -H "Authorization: Bearer dev-key-codespace-001" \
  -d @sample_request.json
```

**Content (quiz generation)** — uses whatever's already been ingested via
`/content/ingest`, so run that first if you haven't:
```bash
curl -X POST http://localhost:8000/content/generate-quiz \
  -H "Content-Type: application/json" -H "Authorization: Bearer dev-key-codespace-001" \
  -d @sample_quiz_request.json
```
Worth checking: are the questions actually grounded in the ingested
content, or does the model wander into generic trivia? Try a topic with
no matching ingested content too, and see if it's honest about that
rather than making things up.

## Where we're at / what's next

- Tutor, Assessment, and Content agents all work end to end.
- Auth + tenant isolation, input validation, error handling, and retries
  on transient model failures are all in place.
- Prompts have gone through a couple rounds of tuning already (scope
  control on the tutor so it doesn't wander into unrelated topics,
  integrity mode so it doesn't hand out answers on graded work).
- Not yet done: Analytics agent, DB-level tenant isolation (row-level
  security - needs Postgres), moving off SQLite/TF-IDF once we need it.

## What error handling and security actually cover now

- Every route requires a valid API key; `tenant_id` comes from the key,
  never from the request body
- Input validation on all requests (blank text, empty rubrics, out-of-range
  values are rejected with a clear 422 before ever reaching the model)
- Model calls automatically retry (up to 2 extra attempts with backoff) on
  transient failures like a dropped connection, before giving up cleanly
- Config/connection failures that aren't transient (missing API key,
  Ollama unreachable after retries) return a clean 503 with a useful message
- Malformed model output (bad JSON) returns a clean 502 instead of crashing
- A catch-all handler so any unexpected error still returns clean JSON,
  logged server-side instead of leaked to the caller

## Known gaps (on purpose, for now)

- Tenant isolation is enforced by the auth layer resolving `tenant_id` from
  the API key, and every DB query filtering by it — but it's still
  application-level, not database-level (no Postgres row-level security
  yet). Good enough for now; worth revisiting before this holds real
  student data at real scale with many institutions.
- API keys are a flat table, no expiry/rotation/scopes - fine for a student
  project, not what a real multi-tenant SaaS would ship long-term.
- Small local models (if using Ollama) are noticeably less consistent at
  following instructions than the hosted models — expect some looseness
  there that a paid model would likely tighten up.
