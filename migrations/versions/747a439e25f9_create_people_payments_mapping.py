"""create people payments mapping

Revision ID: 747a439e25f9
Revises: a0629b1b3edc
Create Date: 2022-12-02 16:02:52.616168

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "747a439e25f9"
down_revision = "a0629b1b3edc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "m_people_payments",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("created_at", sa.DATETIME, nullable=False),
        sa.Column("updated_at", sa.DATETIME, nullable=False),
        sa.Column(
            "payment_id", sa.CHAR(36), sa.ForeignKey("payments.id"), nullable=False
        ),
        sa.Column("people_id", sa.CHAR(36), sa.ForeignKey("people.id"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("m_people_payments")
