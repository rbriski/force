"""create expenses mapping

Revision ID: 87be38757d25
Revises: 43c11dfb78af
Create Date: 2022-12-01 21:56:44.843555

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "87be38757d25"
down_revision = "43c11dfb78af"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "m_people_expenses",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("created_at", sa.DATETIME, nullable=False),
        sa.Column("updated_at", sa.DATETIME, nullable=False),
        sa.Column(
            "expense_id", sa.CHAR(36), sa.ForeignKey("expenses.id"), nullable=False
        ),
        sa.Column("people_id", sa.CHAR(36), sa.ForeignKey("people.id"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("m_people_expenses")
