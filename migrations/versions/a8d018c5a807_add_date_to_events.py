"""add date to events

Revision ID: a8d018c5a807
Revises: 747a439e25f9
Create Date: 2023-01-16 14:24:27.648797

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a8d018c5a807"
down_revision = "747a439e25f9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("events", sa.Column("date", sa.DATE))


def downgrade():
    op.drop_column("events", "date")
