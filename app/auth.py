"""
Authentication.

Every protected route depends on `require_tenant`, which reads the
bearer token, validates it, and returns the tenant_id it belongs to.
Routes use THIS tenant_id for every database query - never one typed
into the request body by the caller. That's what actually prevents one
institution from reading another's data: it's not enough to filter
queries by tenant_id if the tenant_id itself is just whatever the
client claims.

Uses FastAPI's HTTPBearer security scheme rather than a plain header
parameter - this is what makes a proper "Authorize" button (lock icon,
top right) show up in /docs, instead of a per-endpoint text field you'd
otherwise have to fill in on every single request while testing.

This is a minimal API-key scheme, not a production auth system (no key
rotation, no expiry, no scopes/roles). Good enough to stop casual/accidental
cross-tenant access during development; a real deployment would want a
proper identity provider in front of this.
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.db import get_tenant_for_api_key

bearer_scheme = HTTPBearer(
    description="Paste just the API key here (e.g. dev-key-codespace-001) - "
                "no need to type 'Bearer', the docs UI adds that automatically."
)


def require_tenant(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    api_key = credentials.credentials.strip()
    tenant_id = get_tenant_for_api_key(api_key)

    if tenant_id is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return tenant_id
