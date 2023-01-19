"""drop payments mapping table

Revision ID: 43e0242dd936
Revises: 3442f9a90abc
Create Date: 2023-01-17 19:45:16.094700

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "43e0242dd936"
down_revision = "3442f9a90abc"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("m_people_payments")


def downgrade():
    pass
