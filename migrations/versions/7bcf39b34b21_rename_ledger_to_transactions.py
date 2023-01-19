"""rename ledger to transactions

Revision ID: 7bcf39b34b21
Revises: 43e0242dd936
Create Date: 2023-01-18 17:22:56.169902

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7bcf39b34b21"
down_revision = "43e0242dd936"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("ledger", "transactions")
    op.rename_table("m_people_ledger", "m_people_transactions")
    op.alter_column(
        "m_people_transactions", "ledger_id", new_column_name="transaction_id"
    )


def downgrade():
    op.alter_column(
        "m_people_transactions", "transaction_id", new_column_name="ledger_id"
    )
    op.rename_table("transactions", "ledger")
    op.rename_table("m_people_transactions", "m_people_ledger")
