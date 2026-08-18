from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from app.config import settings

# Registers a real OpenAPI "bearerAuth" security scheme, so Swagger's
# Authorize popup shows a field to paste a token into — the manual
# request.headers.get("Authorization") approach this replaces was invisible
# to Swagger since it wasn't a registered security scheme.
_bearer_scheme = HTTPBearer(auto_error=False)

_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(settings.jwt_jwks_url)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


async def verify_jwt(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = credentials.credentials

    try:
        if settings.auth_mode == "dev":
            claims = jwt.decode(
                token, settings.jwt_dev_secret, algorithms=["HS256"],
                audience=settings.jwt_audience, issuer=settings.jwt_issuer,
            )
        else:
            jwks = await _get_jwks()
            claims = jwt.decode(
                token, jwks, algorithms=["RS256"],
                audience=settings.jwt_audience, issuer=settings.jwt_issuer,
            )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if "tenant_id" not in claims or "student_id" not in claims:
        raise HTTPException(status_code=401, detail="Token missing required claims")
    return claims
