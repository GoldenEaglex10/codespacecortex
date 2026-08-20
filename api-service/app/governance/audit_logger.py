from sqlalchemy.ext.asyncio import AsyncSession
from app.data.models.audit_log import AuditLog

async def log_interaction(
    db: AsyncSession, *, tenant_id: str, student_id: str | None, request_id: str,
    question: str | None = None, tools_called: list | None = None, response: str | None = None,
    input_tokens: int | None = None, output_tokens: int | None = None, cost_usd: float | None = None,
):
    entry = AuditLog(
        tenant_id=tenant_id, student_id=student_id, request_id=request_id,
        question=question, tools_called=tools_called, response=response,
        input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=cost_usd,
    )
    db.add(entry)
    await db.flush()
    return entry
