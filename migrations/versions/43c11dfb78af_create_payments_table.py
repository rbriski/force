"""create payments table

Revision ID: 43c11dfb78af
Revises: 209530958db6
Create Date: 2022-12-01 21:52:41.867958

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "43c11dfb78af"
down_revision = "209530958db6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", sa.INTEGER, primary_key=True),
        sa.Column("at_id", sa.VARCHAR),
        sa.Column("created_at", sa.DATETIME, nullable=False),
        sa.Column("updated_at", sa.DATETIME, nullable=False),
        sa.Column("amount", sa.FLOAT),
        sa.Column("description", sa.VARCHAR),
    )


def downgrade() -> None:
    op.drop_table("payments")
