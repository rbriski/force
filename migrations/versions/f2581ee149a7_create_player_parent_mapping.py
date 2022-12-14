"""create player parent  mapping

Revision ID: f2581ee149a7
Revises: 87be38757d25
Create Date: 2022-12-01 21:59:30.645492

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f2581ee149a7"
down_revision = "87be38757d25"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "m_player_parent",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("created_at", sa.DATETIME, nullable=False),
        sa.Column("updated_at", sa.DATETIME, nullable=False),
        sa.Column("player_id", sa.CHAR(36), sa.ForeignKey("people.id"), nullable=False),
        sa.Column("parent_id", sa.CHAR(36), sa.ForeignKey("people.id"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("m_player_parent")
