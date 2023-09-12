"""create track room table

Revision ID: 6661a5931def
Revises: cc5987599bdc
Create Date: 2023-09-12 11:37:30.681814

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6661a5931def'
down_revision = 'cc5987599bdc'
branch_labels = None
depends_on = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_table("track_rooms")
    pass
