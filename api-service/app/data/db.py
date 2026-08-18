from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

admin_engine = create_async_engine(settings.database_url_admin, pool_pre_ping=True)
AdminSessionLocal = async_sessionmaker(admin_engine, expire_on_commit=False)

@asynccontextmanager
async def tenant_session(tenant_id: str):
    async with SessionLocal() as session:
        async with session.begin():
            await session.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": tenant_id})
            yield session
