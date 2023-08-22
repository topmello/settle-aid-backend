"""create user table

Revision ID: 3daa7378f2c1
Revises: 1957ba7ed413
Create Date: 2023-08-23 07:43:58.663837

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3daa7378f2c1'
down_revision = '1957ba7ed413'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer, primary_key=True, index=True),
        sa.Column('username', sa.String, unique=True, nullable=False),
        sa.Column('password', sa.String, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False)
    )
    pass


def downgrade() -> None:
    op.drop_table('users')
    pass
