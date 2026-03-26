"""add runtime config store

Revision ID: 20260326_0003
Revises: 20260325_0002
Create Date: 2026-03-26 00:03:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260326_0003"
down_revision = "20260325_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runtime_config",
        sa.Column("key", sa.String(length=50), nullable=False),
        sa.Column("settings_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("runtime_config")
