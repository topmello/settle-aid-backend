"""create landmark table

Revision ID: f41f135d6d21
Revises: 3daa7378f2c1
Create Date: 2023-08-23 14:30:46.255610

"""
from alembic import op
import sqlalchemy as sa
from app.models import Landmark


# revision identifiers, used by Alembic.
revision = 'f41f135d6d21'
down_revision = '3daa7378f2c1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    Landmark.__table__.create(op.get_bind())
    pass


def downgrade() -> None:
    Landmark.__table__.drop(op.get_bind())
    pass
