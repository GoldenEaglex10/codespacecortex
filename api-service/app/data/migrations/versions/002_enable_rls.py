"""enable rls

Revision ID: 002
Revises: 001
Create Date: 2026-08-12

"""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

TENANT_TABLES = ["students", "courses", "lessons", "quiz_history", "audit_log", "course_embeddings"]


def upgrade():
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY tenant_isolation_{table}
            ON {table}
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """)
    op.execute("GRANT USAGE ON SCHEMA public TO cortex_app;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cortex_app;")


def downgrade():
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
