"""create roster table

Revision ID: 209530958db6
Revises: e42058c7a40d
Create Date: 2022-12-01 21:47:28.949876

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "209530958db6"
down_revision = "e42058c7a40d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "people",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("at_id", sa.VARCHAR),
        sa.Column("created_at", sa.DATETIME, nullable=False),
        sa.Column("updated_at", sa.DATETIME, nullable=False),
        sa.Column("name", sa.VARCHAR),
        sa.Column("description", sa.VARCHAR),
        sa.Column("email", sa.VARCHAR),
        sa.Column("phone", sa.VARCHAR),
    )


def downgrade() -> None:
    op.drop_table("people")
