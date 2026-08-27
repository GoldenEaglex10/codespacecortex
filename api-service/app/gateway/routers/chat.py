from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.gateway.dependencies.tenant import get_tenant_db, get_current_claims
from app.gateway.dependencies.rate_limit import rate_limit
from app.gateway.dependencies.cache import get_cached_response, set_cached_response

router = APIRouter()


@router.post("/v1/chat", dependencies=[Depends(rate_limit)])
async def chat(
    payload: dict,
    db: AsyncSession = Depends(get_tenant_db),
    claims: dict = Depends(get_current_claims),
):
    question = str(payload.get("question", ""))

    cached = await get_cached_response(claims["tenant_id"], question)
    if cached is not None:
        return {**cached, "cached": True}

    # TODO: this is where the real orchestrator/LLM call will go once wired up.
    # Caching is applied around this stub now so the pattern is already in
    # place for when this becomes an actual (slow, costly) model call.
    response = {
        "tenant_id": claims["tenant_id"],
        "student_id": claims["student_id"],
        "message": "stub response — orchestrator not yet wired",
    }
    await set_cached_response(claims["tenant_id"], question, response)
    return {**response, "cached": False}
