"""
Verifies the app-level API key gateway (app/gateway/dependencies/api_key.py).

Unlike test_tenant_isolation.py, these tests go through the actual HTTP layer
via Starlette's TestClient, since the API key is enforced as a FastAPI
`dependencies=[...]` on the whole app — there's no meaningful way to test it
by calling Python functions directly, it only exists at the request layer.

No real Postgres/Redis calls happen here: /health touches neither, and every
case below is rejected before any route body ever runs.
"""
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_health_without_api_key_is_rejected():
    r = client.get("/health")
    assert r.status_code == 403


def test_health_with_wrong_api_key_is_rejected():
    r = client.get("/health", headers={"X-API-Key": "definitely_wrong"})
    assert r.status_code == 403


def test_health_with_correct_api_key_succeeds():
    r = client.get("/health", headers={"X-API-Key": settings.api_key})
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_chat_without_api_key_is_rejected_before_auth_even_runs():
    # No X-API-Key AND no bearer token — should fail on the API key check
    # (403), not the JWT check (401), since the API key gate runs first.
    r = client.post("/v1/chat", json={"question": "hi"})
    assert r.status_code == 403


def test_chat_with_api_key_but_no_token_is_unauthorized():
    r = client.post(
        "/v1/chat",
        headers={"X-API-Key": settings.api_key},
        json={"question": "hi"},
    )
    assert r.status_code == 401
