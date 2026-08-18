import asyncio, uuid
from app.data.db import AdminSessionLocal
from app.data.models.tenant import Tenant
from app.data.models.student import Student

async def seed():
    async with AdminSessionLocal() as session:
        async with session.begin():
            tenant_a = Tenant(id=uuid.uuid4(), name="Fake Tenant A")
            tenant_b = Tenant(id=uuid.uuid4(), name="Fake Tenant B")
            session.add_all([tenant_a, tenant_b])
            await session.flush()
            session.add_all([
                Student(tenant_id=tenant_a.id, external_id="s1", display_name="Student A1"),
                Student(tenant_id=tenant_b.id, external_id="s1", display_name="Student B1"),
            ])
        print(f"TENANT_A_ID={tenant_a.id}")
        print(f"TENANT_B_ID={tenant_b.id}")

if __name__ == "__main__":
    asyncio.run(seed())
