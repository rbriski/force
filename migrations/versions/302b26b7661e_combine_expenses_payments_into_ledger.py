"""combine expenses/payments into ledger

Revision ID: 302b26b7661e
Revises: 20702fd78471
Create Date: 2023-01-17 19:37:55.087057

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "302b26b7661e"
down_revision = "20702fd78471"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("expenses", sa.Column("debit", sa.BOOLEAN))
    op.rename_table("expenses", "ledger")
    op.drop_table("payments")


def downgrade():
    pass
