from fastapi import Depends
from app.gateway.dependencies.auth import verify_jwt
from app.data.db import tenant_session

async def get_tenant_db(claims: dict = Depends(verify_jwt)):
    async with tenant_session(claims["tenant_id"]) as session:
        yield session

async def get_current_claims(claims: dict = Depends(verify_jwt)) -> dict:
    return claims
