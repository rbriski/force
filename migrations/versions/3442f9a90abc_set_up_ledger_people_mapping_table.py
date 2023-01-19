"""set up ledger/people mapping table

Revision ID: 3442f9a90abc
Revises: 302b26b7661e
Create Date: 2023-01-17 19:42:48.509238

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3442f9a90abc"
down_revision = "302b26b7661e"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("m_people_expenses", "people_id", new_column_name="person_id")
    op.alter_column("m_people_expenses", "expense_id", new_column_name="ledger_id")
    op.rename_table("m_people_expenses", "m_people_ledger")


def downgrade():
    pass
