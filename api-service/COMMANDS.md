# Cortex — Commands Reference

Everything needed to clone, set up, run, test, and troubleshoot this project.
All commands are shown for **PowerShell (Windows)**. If you're on macOS/Linux,
swap `Copy-Item` for `cp` and `Get-Content x -Raw | cmd` for `cmd < x`.

> **The API is private.** Every route — including `/health` — now requires an
> `X-API-Key` header matching `API_KEY` in `.env`. Requests without it get a
> `403`, not a normal error response. This is separate from JWT auth: the API
> key gates "can you reach this API at all," the JWT gates "which tenant are
> you." See Section 9 for details.

---

## 0. Prerequisites

- Docker Desktop installed and running (`docker info` should succeed, not error)
- Git installed

---

## 1. First-time setup (new machine / fresh clone)

```powershell
# Clone the repo
git clone <your-repo-url>
cd codespace-cortex

# Recreate your local .env (never committed — it's gitignored)
Copy-Item .env.example .env
# Then open .env and set your own API_KEY and JWT_DEV_SECRET values —
# the .example file ships with placeholder values, not real secrets.

# Build and start everything (app, postgres, redis)
docker compose up -d --build

# Check all 3 containers are healthy
docker compose ps
# app       -> should show 0.0.0.0:8000->8000/tcp
# postgres  -> should show NO port mapping (private, by design)
# redis     -> should show NO port mapping (private, by design)
```

### Create the restricted DB role (required once per fresh Postgres volume)
```powershell
Get-Content scripts/create_app_role.sql -Raw | docker compose exec -T postgres psql -U cortex -d cortex
```
Verify:
```powershell
docker compose exec postgres psql -U cortex -d cortex -c "\du"
```
You should see `cortex_app` in the role list.

### Run database migrations (required once per fresh Postgres volume)
```powershell
docker compose exec app alembic upgrade head
```
Creates all tables, enables row-level security (RLS), enables the pgvector extension.

### Seed two fake tenants for local dev/testing
```powershell
docker compose exec app python -m scripts.seed_dev_tenant
```
Prints `TENANT_A_ID` and `TENANT_B_ID` — copy these if you need them for manual testing.

---

## 2. Everyday commands (once already set up)

```powershell
# Start containers (if stopped)
docker compose up -d

# Stop containers (keeps data)
docker compose stop

# Stop and remove containers (keeps data — volumes persist)
docker compose down

# Stop and WIPE all data (fresh Postgres/Redis next start)
docker compose down -v

# View logs
docker compose logs -f app

# Rebuild after changing requirements.txt or Dockerfile
docker compose up -d --build

# Restart just the app (e.g. after editing pytest.ini, which isn't volume-mounted)
docker compose restart app
```

> Note: `./app` is volume-mounted into the container, so editing files under
> `app/` on your host takes effect immediately (or after `docker compose restart app`
> for uvicorn to pick it up) — no rebuild needed. Editing `requirements.txt`,
> `Dockerfile`, or `pytest.ini` DOES require `docker compose up -d --build`.

---

## 3. Verify the app is working

```powershell
# Health check — needs the API key now
curl.exe http://localhost:8000/health -H "X-API-Key: <your API_KEY from .env>"
# Expect: {"status":"ok"}

# Without the key — should be rejected
curl.exe http://localhost:8000/health
# Expect: 403 {"detail":"Invalid or missing API key"}
```

---

## 4. Running tests

```powershell
# Run the tenant-isolation security suite
docker compose exec app pytest tests/security/test_tenant_isolation.py -v

# Run the API-key gateway tests
docker compose exec app pytest tests/security/test_api_key.py -v

# Run everything
docker compose exec app pytest tests/security/ -v
docker compose exec app pytest -v
```

---

## 5. Database access (debugging)

Never expose Postgres/Redis ports — always go through `docker compose exec`:

```powershell
# Open a psql shell inside the container
docker compose exec postgres psql -U cortex -d cortex

# Run a single SQL file against the DB
Get-Content path/to/file.sql -Raw | docker compose exec -T postgres psql -U cortex -d cortex

# Open a Redis CLI shell
docker compose exec redis redis-cli
```

---

## 6. Git workflow

```powershell
git status
git add .
git commit -m "Describe what changed"
git push

# On a new machine, after cloning:
git pull
```

> Reminder: `.env` is gitignored on purpose (it holds secrets). It will
> NEVER come across via `git clone`/`git pull` — always recreate it from
> `.env.example` on every new machine (see Section 1), and set your own
> `API_KEY` / `JWT_DEV_SECRET` values each time.

---

## 7. Full end-to-end request (API key + JWT + hitting /v1/chat)

```powershell
# 1. Get a real tenant ID
docker compose exec app python -m scripts.seed_dev_tenant
# copy the TENANT_A_ID it prints

# 2. Mint a JWT for that tenant
$token = docker compose exec app python -m scripts.mint_test_token <TENANT_A_ID> s1

# 3. Call /v1/chat with BOTH the API key and the bearer token
$headers = @{
    "X-API-Key"     = "<your API_KEY from .env>"
    "Authorization" = "Bearer $token"
}
$body = @{ question = "hello" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/v1/chat" -Method Post -Headers $headers -Body $body -ContentType "application/json"

# 4. Run it again with the SAME question — the response now comes from
#    Redis cache instead of being recomputed. Look for "cached": true.
Invoke-RestMethod -Uri "http://localhost:8000/v1/chat" -Method Post -Headers $headers -Body $body -ContentType "application/json"
```

---

## 8. Browsing the API docs

`/docs`, `/redoc`, and `/openapi.json` only work when `ENVIRONMENT=dev` in
`.env` — they're disabled entirely otherwise (a private API shouldn't
advertise its own shape). In dev mode:

- Open `http://localhost:8000/docs`
- Click **Authorize** — you'll now see TWO fields (this didn't exist before
  the auth.py rewrite): one for the API key, one for the bearer token. Fill
  in both, click Authorize, then try any endpoint directly in the browser.

---

## 9. What changed: private API + caching (summary)

| Change | File(s) | What it does |
|---|---|---|
| App-level API key | `app/gateway/dependencies/api_key.py`, `app/main.py` | Every route requires `X-API-Key`, applied globally — including `/health` |
| Docs hidden outside dev | `app/main.py` | `/docs`, `/redoc`, `/openapi.json` return 404 unless `ENVIRONMENT=dev` |
| Swagger Authorize button fixed | `app/gateway/dependencies/auth.py` | Switched from manual header parsing to FastAPI's `HTTPBearer`, which registers a real OpenAPI security scheme |
| Redis response caching | `app/gateway/dependencies/cache.py`, `app/gateway/routers/chat.py` | Identical (tenant, question) pairs are served from Redis instead of recomputed, TTL from `CACHE_TTL_SECONDS` |
| New env vars | `.env`, `.env.example`, `app/config.py` | `API_KEY`, `ENVIRONMENT`, `CACHE_TTL_SECONDS` |
| New test file | `tests/security/test_api_key.py` | Verifies the API key gateway rejects/accepts correctly |

No new pip packages were required — everything used (`fastapi.security`,
`redis.asyncio`) was already in `requirements.txt`.

---

## 10. Common errors & fixes

### `docker compose exec ... < file.sql` fails with "the '<' operator is reserved"
You're in PowerShell, which doesn't support `<` redirection. Use instead:
```powershell
Get-Content file.sql -Raw | docker compose exec -T postgres psql -U cortex -d cortex
```

### `pip install` fails with "THESE PACKAGES DO NOT MATCH THE HASHES"
Usually a corrupted cached layer from a flaky network mid-download. Fix:
```powershell
docker builder prune -f
docker compose build --no-cache app
docker compose up -d
```

### `syntax error at or near "$1"` on `SET LOCAL app.tenant_id = $1`
Postgres doesn't support bind parameters in `SET`/`SET LOCAL`. Fixed in
`app/data/db.py` by using `SELECT set_config('app.tenant_id', :tid, true)`
instead.

### `RuntimeError: ... attached to a different loop` in pytest
Async event loop scope mismatch. Fixed via `asyncio_default_fixture_loop_scope
= session` in `pytest.ini`, plus an autouse `engine.dispose()` fixture in
`tests/conftest.py` that forces fresh connections per test.

### `403 Invalid or missing API key`
You forgot the `X-API-Key` header, or it doesn't match `API_KEY` in `.env`.
This is new — every route requires it now, including `/health`.

### `curl.exe` mangles quotes / `Invoke-WebRequest: Cannot bind parameter 'Headers'`
`curl` in PowerShell is aliased to `Invoke-WebRequest`, which has different
syntax. Either call the real binary explicitly (`curl.exe ...`) with single
quotes around the JSON body, or use `Invoke-RestMethod` with a `@{}` hashtable
for headers — the latter is more reliable, see Section 7 above.

---

## 11. Full command sequence, start to finish (copy-paste block)

```powershell
git clone <your-repo-url>
cd codespace-cortex
Copy-Item .env.example .env
# edit .env: set your own API_KEY and JWT_DEV_SECRET
docker compose up -d --build
Get-Content scripts/create_app_role.sql -Raw | docker compose exec -T postgres psql -U cortex -d cortex
docker compose exec app alembic upgrade head
docker compose exec app python -m scripts.seed_dev_tenant
curl.exe http://localhost:8000/health -H "X-API-Key: <your API_KEY>"
docker compose exec app pytest tests/security/ -v
```
