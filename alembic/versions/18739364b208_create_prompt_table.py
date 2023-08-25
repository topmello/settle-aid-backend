"""create prompt table

Revision ID: 18739364b208
Revises: 9ef32f023bf6
Create Date: 2023-08-26 08:04:47.306875

"""
from alembic import op
import sqlalchemy as sa
from app.models import Prompt


# revision identifiers, used by Alembic.
revision = '18739364b208'
down_revision = '9ef32f023bf6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    Prompt.__table__.create(op.get_bind())
    pass


def downgrade() -> None:
    Prompt.__table__.drop(op.get_bind())
    pass
