"""create restaurant table

Revision ID: cf80ef5b269e
Revises: f41f135d6d21
Create Date: 2023-08-24 12:23:15.104409

"""
from alembic import op
import sqlalchemy as sa
from app.models import Restaurant


# revision identifiers, used by Alembic.
revision = 'cf80ef5b269e'
down_revision = 'f41f135d6d21'
branch_labels = None
depends_on = None


def upgrade() -> None:
    Restaurant.__table__.create(op.get_bind())
    pass


def downgrade() -> None:
    Restaurant.__table__.drop(op.get_bind())
    pass
