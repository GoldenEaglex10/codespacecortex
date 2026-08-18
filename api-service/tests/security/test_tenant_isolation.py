import pytest
from sqlalchemy import text
from app.data.db import SessionLocal, tenant_session

pytestmark = pytest.mark.asyncio

async def test_cannot_read_other_tenant_data(seeded_tenants):
    tenant_a, tenant_b = seeded_tenants
    async with tenant_session(str(tenant_a.id)) as db:
        result = await db.execute(text("SELECT tenant_id FROM students"))
        rows = result.fetchall()
        assert all(str(r.tenant_id) == str(tenant_a.id) for r in rows)
        assert not any(str(r.tenant_id) == str(tenant_b.id) for r in rows)

async def test_cannot_write_into_other_tenant(seeded_tenants):
    tenant_a, tenant_b = seeded_tenants
    async with tenant_session(str(tenant_a.id)) as db:
        with pytest.raises(Exception):
            await db.execute(
                text("INSERT INTO students (tenant_id, external_id, display_name) VALUES (:tid, 'x', 'x')"),
                {"tid": str(tenant_b.id)},
            )

async def test_unscoped_session_sees_nothing(seeded_tenants):
    async with SessionLocal() as db:
        async with db.begin():
            result = await db.execute(text("SELECT * FROM students"))
            assert result.fetchall() == []
