from fastapi import Depends, FastAPI
from app.config import settings
from app.gateway.dependencies.api_key import verify_api_key
from app.gateway.routers import health, chat

# Outside "dev" mode, hide the interactive docs entirely — a private API
# shouldn't advertise its own shape to anyone who finds the port open.
_docs_kwargs = (
    {}
    if settings.environment == "dev"
    else {"docs_url": None, "redoc_url": None, "openapi_url": None}
)

app = FastAPI(
    title="Codespace Cortex",
    # Applied globally: every route on this app requires a valid X-API-Key,
    # including /health. This is what makes the API "private" — JWT auth
    # (see auth.py) is a second, separate layer on top of this for routes
    # that also need to know which tenant/student is calling.
    dependencies=[Depends(verify_api_key)],
    **_docs_kwargs,
)

app.include_router(health.router)
app.include_router(chat.router)
