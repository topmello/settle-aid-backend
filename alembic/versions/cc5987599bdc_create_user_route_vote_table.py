"""create user route vote table

Revision ID: cc5987599bdc
Revises: faf5ceba2843
Create Date: 2023-09-09 15:14:59.592141

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc5987599bdc'
down_revision = 'faf5ceba2843'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_route_votes',
        sa.Column('user_id', sa.Integer, sa.ForeignKey(
            'users.user_id'), nullable=False, primary_key=True),
        sa.Column('route_id', sa.Integer, sa.ForeignKey(
            'routes.route_id'), nullable=False, primary_key=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("now()"), nullable=False)
    )
    pass


def downgrade() -> None:
    op.drop_table('user_route_votes')
    pass
