"""add route table

Revision ID: faf5ceba2843
Revises: 9c12b52d52a9
Create Date: 2023-09-09 12:58:46.505453

"""
from alembic import op
import sqlalchemy as sa
from app.models import Route


# revision identifiers, used by Alembic.
revision = 'faf5ceba2843'
down_revision = '9c12b52d52a9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    Route.__table__.create(op.get_bind())
    pass


def downgrade() -> None:
    Route.__table__.drop(op.get_bind())
    pass
