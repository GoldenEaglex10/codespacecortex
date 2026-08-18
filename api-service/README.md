# Codespace Cortex — Data Layer & Gateway

Only the API gateway is exposed to the outside world. Postgres and Redis are
private — reachable only from inside the Docker network, never from the host
machine or the internet.

```
Outside world
      │
      ▼  port 8000 (published)
   ┌──────┐
   │ app  │  ← the only public surface
   └──┬───┘
      │  internal Docker network only
      ├────────► postgres  (no published port)
      └────────► redis     (no published port)
```

## What's in here

```
codespace-cortex/
├── Dockerfile                           # builds the app container
├── docker-compose.yml                   # app (public) + postgres/redis (private)
├── requirements.txt
├── .env / .env.example                  # uses "postgres"/"redis" as hostnames, not localhost
├── alembic.ini
├── pytest.ini
├── app/
│   ├── main.py
│   ├── config.py
│   ├── data/                            # db.py, models/, migrations/
│   ├── gateway/                         # dependencies/, routers/
│   └── governance/                      # audit_logger.py, cost_metering.py
├── scripts/                             # create_app_role.sql, seed_dev_tenant.py, mint_test_token.py
└── tests/security/test_tenant_isolation.py
```

## Setup (Docker Desktop)

1. Start Docker Desktop, confirm it's running: `docker info`
2. Build and start everything:
   ```bash
   docker compose up -d --build
   ```
3. Check status:
   ```bash
   docker compose ps
   ```
   Only `app` shows a host port (`0.0.0.0:8000->8000/tcp`). `postgres` and `redis`
   show no host port mapping at all — that's the private part working.
4. Create the restricted app database role (one-time):
   ```bash
   docker compose exec -T postgres psql -U cortex -d cortex < scripts/create_app_role.sql
   ```
5. Run migrations — **from inside the app container**, since Postgres isn't reachable from your host anymore:
   ```bash
   docker compose exec app alembic upgrade head
   ```
6. Seed two fake tenants:
   ```bash
   docker compose exec app python -m scripts.seed_dev_tenant
   ```
   Copy the two printed UUIDs.

## Test

Only port 8000 is reachable from your machine — this is the point:
```bash
curl http://localhost:8000/health
```

Everything else runs inside the container:
```bash
TOKEN=$(docker compose exec app python -m scripts.mint_test_token <TENANT_A_ID>)
curl -X POST http://localhost:8000/v1/chat \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{}'

docker compose exec app pytest tests/security/ -v
```

Prove Postgres/Redis are actually private — these should FAIL from your host machine:
```bash
psql -h localhost -p 5432 -U cortex -d cortex     # connection refused
redis-cli -h localhost -p 6379 ping               # connection refused
```

## Request contract

1. Client sends `Authorization: Bearer <JWT>` to the gateway on port 8000 — the only reachable port.
2. `verify_jwt` checks signature, audience, issuer, expiry; pulls `tenant_id` + `student_id`.
3. `rate_limit` checks a Redis counter per tenant+student; 429 if over limit.
4. `get_tenant_db` opens a transaction, runs `SET LOCAL app.tenant_id = <id>`, hands back
   a database session scoped by Postgres row-level security for the rest of the request.
5. Route handler runs inside that transaction — every query is automatically tenant-scoped.
6. Handler can call `governance.audit_logger.log_interaction(...)` in the same transaction.

Do not read tables directly or pass `tenant_id` by hand anywhere downstream —
always go through `get_tenant_db` / `tenant_session`. Do not add a `ports:` entry
to `postgres` or `redis` in docker-compose.yml — that reopens the exact hole this
setup closes.
