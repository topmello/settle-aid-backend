"""bridging entity for prompt landmark

Revision ID: 26743ad27b0a
Revises: 18739364b208
Create Date: 2023-08-26 08:11:44.437686

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26743ad27b0a'
down_revision = '18739364b208'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prompt_landmarks",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("prompt_id", sa.Integer, sa.ForeignKey("prompts.prompt_id"), nullable=False),
        sa.Column("created_by_user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("location_id", sa.Integer, sa.ForeignKey("landmarks.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False)
    )

    op.create_table(
        "prompt_landmark_votes",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("prompt_location_id", sa.Integer, sa.ForeignKey("prompt_landmarks.id"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("vote", sa.Boolean, nullable=False), # True for upvote, False for downvote
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False)
    )
    pass


def downgrade() -> None:
    op.drop_table("prompt_landmark_votes")
    op.drop_table("prompt_landmarks")
    
    pass
