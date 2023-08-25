"""create grocery and pharmacy tables

Revision ID: 9ef32f023bf6
Revises: cf80ef5b269e
Create Date: 2023-08-26 08:00:42.004426

"""
from alembic import op
import sqlalchemy as sa
from app.models import Grocery, Pharmacy


# revision identifiers, used by Alembic.
revision = '9ef32f023bf6'
down_revision = 'cf80ef5b269e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    Grocery.__table__.create(op.get_bind())
    Pharmacy.__table__.create(op.get_bind())
    pass


def downgrade() -> None:
    Grocery.__table__.drop(op.get_bind())
    Pharmacy.__table__.drop(op.get_bind())
    pass
