import pytest_asyncio
import uuid
from app.data.db import AdminSessionLocal, engine, admin_engine
from app.data.models.tenant import Tenant
from app.data.models.student import Student

@pytest_asyncio.fixture(autouse=True)
async def _dispose_engines_after_test():
    """Force fresh DB connections per test, avoiding stale connections
    left over from a previous test's (now-closed) event loop."""
    yield
    await engine.dispose()
    await admin_engine.dispose()

@pytest_asyncio.fixture
async def seeded_tenants():
    async with AdminSessionLocal() as session:
        async with session.begin():
            tenant_a = Tenant(id=uuid.uuid4(), name="Test Tenant A")
            tenant_b = Tenant(id=uuid.uuid4(), name="Test Tenant B")
            session.add_all([tenant_a, tenant_b])
            await session.flush()
            session.add(Student(tenant_id=tenant_a.id, external_id="t1", display_name="A1"))
            session.add(Student(tenant_id=tenant_b.id, external_id="t1", display_name="B1"))
    yield tenant_a, tenant_b