"""create expenses table

Revision ID: e42058c7a40d
Revises: 
Create Date: 2022-12-01 21:24:06.407798

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e42058c7a40d"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "expenses",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("at_id", sa.VARCHAR),
        sa.Column("event_id", sa.CHAR(36), sa.ForeignKey("events.id")),
        sa.Column("created_at", sa.DATETIME, nullable=False),
        sa.Column("updated_at", sa.DATETIME, nullable=False),
        sa.Column("amount", sa.FLOAT),
        sa.Column("description", sa.VARCHAR),
    )


def downgrade() -> None:
    op.drop_table("expenses")
