"""pgvector setup

Revision ID: 003
Revises: 002
Create Date: 2026-08-12

"""
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def downgrade():
    op.execute("DROP EXTENSION IF EXISTS vector;")
