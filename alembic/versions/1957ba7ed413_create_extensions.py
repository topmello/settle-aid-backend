"""create extensions

Revision ID: 1957ba7ed413
Revises: 
Create Date: 2023-08-23 07:43:04.212442

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1957ba7ed413'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    pass


def downgrade() -> None:
    pass
