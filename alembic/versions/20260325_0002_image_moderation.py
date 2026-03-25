"""add image moderation fields

Revision ID: 20260325_0002
Revises: 20260325_0001
Create Date: 2026-03-25 00:02:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_0002"
down_revision = "20260325_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("images", sa.Column("moderation_status", sa.String(length=50), nullable=False, server_default="generated"))
    op.add_column("images", sa.Column("moderation_notes", sa.Text(), nullable=True))
    op.alter_column("images", "moderation_status", server_default=None)


def downgrade() -> None:
    op.drop_column("images", "moderation_notes")
    op.drop_column("images", "moderation_status")
