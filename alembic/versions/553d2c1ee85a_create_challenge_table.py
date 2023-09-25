"""create challenge table

Revision ID: 553d2c1ee85a
Revises: 6ba87637e898
Create Date: 2023-09-25 10:29:07.214752

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '553d2c1ee85a'
down_revision = '6ba87637e898'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "challenges",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("grade", sa.Integer, nullable=False),
        sa.Column("score", sa.Float, nullable=False)
    )

    op.create_table(
        "user_challenges",
        sa.Column("user_id", sa.Integer, sa.ForeignKey(
            'users.user_id', ondelete="CASCADE"), nullable=False, primary_key=True),
        sa.Column("challenge_id", sa.Integer, sa.ForeignKey(
            'challenges.id', ondelete="CASCADE"), nullable=False, primary_key=True),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("month", sa.Integer, nullable=False),
        sa.Column("day", sa.Integer, nullable=False),
        sa.Column("progress", sa.Float, nullable=False, default=0.0),
        # Adding the unique constraint
        sa.UniqueConstraint('user_id', 'challenge_id', 'year',
                            'month', 'day', name='uix_user_challenge_date'),
        # Adding the composite index
        sa.Index('idx_year_month_day', 'year', 'month', 'day')
    )
    pass


def downgrade() -> None:
    op.drop_table("user_challenges")
    op.drop_table("challenges")
    pass
