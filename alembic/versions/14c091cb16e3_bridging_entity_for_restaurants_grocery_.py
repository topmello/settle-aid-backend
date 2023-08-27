"""bridging entity for restaurants, grocery, pharmacy

Revision ID: 14c091cb16e3
Revises: 26743ad27b0a
Create Date: 2023-08-26 08:51:57.479083

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '14c091cb16e3'
down_revision = '26743ad27b0a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prompt_restaurants",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("prompt_id", sa.Integer, sa.ForeignKey("prompts.prompt_id"), nullable=False),
        sa.Column("created_by_user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("location_id", sa.Integer, sa.ForeignKey("restaurants.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False)
    )

    op.create_table(
        "prompt_restaurant_votes",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("prompt_location_id", sa.Integer, sa.ForeignKey("prompt_restaurants.id"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("vote", sa.Boolean, nullable=False), # True for upvote, False for downvote
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False)
    )
    op.create_table(
        "prompt_groceries",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("prompt_id", sa.Integer, sa.ForeignKey("prompts.prompt_id"), nullable=False),
        sa.Column("created_by_user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("location_id", sa.Integer, sa.ForeignKey("groceries.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False)
    )
    op.create_table(
        "prompt_grocery_votes",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("prompt_location_id", sa.Integer, sa.ForeignKey("prompt_groceries.id"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("vote", sa.Boolean, nullable=False), # True for upvote, False for downvote
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False)
    )
    op.create_table(
        "prompt_pharmacies",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("prompt_id", sa.Integer, sa.ForeignKey("prompts.prompt_id"), nullable=False),
        sa.Column("created_by_user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("location_id", sa.Integer, sa.ForeignKey("pharmacies.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False)
    )
    op.create_table(
        "prompt_pharmacy_votes",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("prompt_location_id", sa.Integer, sa.ForeignKey("prompt_pharmacies.id"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("vote", sa.Boolean, nullable=False), # True for upvote, False for downvote
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False)
    )

    pass


def downgrade() -> None:
    op.drop_table("prompt_restaurant_votes")
    op.drop_table("prompt_restaurants")
    op.drop_table("prompt_grocery_votes")
    op.drop_table("prompt_groceries")
    op.drop_table("prompt_pharmacy_votes")
    op.drop_table("prompt_pharmacies")
    

    pass
