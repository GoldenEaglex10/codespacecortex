from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from app.config import settings

# Registers "X-API-Key" as a real OpenAPI security scheme, so Swagger's
# Authorize popup shows a field for it (same reasoning as HTTPBearer in auth.py).
_api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: str | None = Depends(_api_key_scheme)) -> None:
    """
    Gateway-level check: is this caller allowed to talk to the API at all?

    This is intentionally separate from JWT auth (app/gateway/dependencies/auth.py):
      - API key  -> "is this caller allowed to reach this API at all"
      - JWT      -> "which tenant/student is making this specific request"

    Applied globally in app/main.py so it covers EVERY route, including /health —
    without a valid key, nobody outside can even confirm the API exists.
    """
    if not settings.api_key:
        # Fails closed: if no API_KEY is configured, refuse everything rather
        # than silently running wide open.
        raise HTTPException(status_code=500, detail="Server misconfigured: API_KEY not set")
    if key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
