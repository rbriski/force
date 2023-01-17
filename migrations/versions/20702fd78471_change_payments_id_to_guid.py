"""change payments ID to guid

Revision ID: 20702fd78471
Revises: a8d018c5a807
Create Date: 2023-01-16 19:24:06.340063

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20702fd78471"
down_revision = "a8d018c5a807"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("payments")
    op.create_table(
        "payments",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("at_id", sa.VARCHAR),
        sa.Column("created_at", sa.DATETIME, nullable=False),
        sa.Column("updated_at", sa.DATETIME, nullable=False),
        sa.Column("amount", sa.FLOAT),
        sa.Column("description", sa.VARCHAR),
    )


def downgrade():
    pass
