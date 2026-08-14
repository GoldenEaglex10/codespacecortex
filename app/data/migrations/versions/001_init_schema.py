"""init schema

Revision ID: 001
Revises:
Create Date: 2026-08-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tenants",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "students",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("external_id", sa.String, nullable=False),
        sa.Column("display_name", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_students_tenant", "students", ["tenant_id"])
    op.create_unique_constraint("uq_students_tenant_external", "students", ["tenant_id", "external_id"])

    op.create_table(
        "courses",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("title", sa.String, nullable=False),
    )
    op.create_index("ix_courses_tenant", "courses", ["tenant_id"])

    op.create_table(
        "lessons",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("course_id", pg.UUID(as_uuid=True), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
    )
    op.create_index("ix_lessons_tenant", "lessons", ["tenant_id"])

    op.create_table(
        "quiz_history",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("student_id", pg.UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("lesson_id", pg.UUID(as_uuid=True), sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("taken_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_quiz_history_tenant", "quiz_history", ["tenant_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("student_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("request_id", sa.String, nullable=False),
        sa.Column("question", sa.Text, nullable=True),
        sa.Column("tools_called", pg.JSONB, nullable=True),
        sa.Column("response", sa.Text, nullable=True),
        sa.Column("input_tokens", sa.Integer, nullable=True),
        sa.Column("output_tokens", sa.Integer, nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_log_tenant", "audit_log", ["tenant_id"])

    op.create_table(
        "course_embeddings",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("course_id", pg.UUID(as_uuid=True), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("embedding", pg.ARRAY(sa.Float), nullable=False),
    )
    op.create_index("ix_course_embeddings_tenant", "course_embeddings", ["tenant_id"])


def downgrade():
    for t in ["course_embeddings", "audit_log", "quiz_history", "lessons", "courses", "students", "tenants"]:
        op.drop_table(t)
