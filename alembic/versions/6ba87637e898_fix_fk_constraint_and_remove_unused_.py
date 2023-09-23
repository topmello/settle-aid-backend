"""fix fk constraint and remove unused table

Revision ID: 6ba87637e898
Revises: 6661a5931def
Create Date: 2023-09-23 13:07:43.562122

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '6ba87637e898'
down_revision = '6661a5931def'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("track_rooms")
    op.drop_table("refresh_tokens")

    op.drop_table('user_route_votes')
    op.create_table(
        'user_route_votes',
        sa.Column('user_id', sa.Integer, sa.ForeignKey(
            'users.user_id', ondelete="CASCADE"), nullable=False, primary_key=True),
        sa.Column('route_id', sa.Integer, sa.ForeignKey(
            'routes.route_id', ondelete="CASCADE"), nullable=False, primary_key=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("now()"), nullable=False)
    )

    pass


def downgrade() -> None:

    op.drop_table('user_route_votes')

    op.create_table(
        'user_route_votes',
        sa.Column('user_id', sa.Integer, sa.ForeignKey(
            'users.user_id'), nullable=False, primary_key=True),
        sa.Column('route_id', sa.Integer, sa.ForeignKey(
            'routes.route_id'), nullable=False, primary_key=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("now()"), nullable=False)
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("user_id", sa.Integer, sa.ForeignKey(
            'users.user_id'), nullable=False, primary_key=True),
        sa.Column("token", sa.String, nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False)
    )

    op.create_table(
        "track_rooms",
        sa.Column("room_id", sa.String, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey(
            "users.user_id"), nullable=False),
        sa.Column("pin", sa.String, nullable=False),
        sa.Column("failed_attempts", sa.Integer, nullable=False, default=0),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    pass
