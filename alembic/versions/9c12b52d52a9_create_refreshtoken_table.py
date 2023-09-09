"""create refreshtoken table

Revision ID: 9c12b52d52a9
Revises: 14c091cb16e3
Create Date: 2023-09-07 18:48:05.148262

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c12b52d52a9'
down_revision = '14c091cb16e3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("user_id", sa.Integer, sa.ForeignKey(
            'users.user_id'), nullable=False, primary_key=True),
        sa.Column("token", sa.String, nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False)
    )
    pass


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    pass
