"""create events table

Revision ID: a0629b1b3edc
Revises: f2581ee149a7
Create Date: 2022-12-01 22:00:16.802645

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a0629b1b3edc"
down_revision = "f2581ee149a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("at_id", sa.VARCHAR),
        sa.Column("created_at", sa.DATETIME, nullable=False),
        sa.Column("updated_at", sa.DATETIME, nullable=False),
        sa.Column("name", sa.VARCHAR),
        sa.Column("description", sa.VARCHAR),
    )


def downgrade() -> None:
    op.drop_table("events")
