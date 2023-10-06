"""add route images table

Revision ID: ffd40eb69bae
Revises: 553d2c1ee85a
Create Date: 2023-10-06 10:20:55.101954

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ffd40eb69bae'
down_revision = '553d2c1ee85a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "route_images",
        sa.Column(
            "route_id",
            sa.Integer,
            sa.ForeignKey("routes.route_id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False
        ),
        sa.Column("route_image_name", sa.String, nullable=False)
    )
    pass


def downgrade() -> None:
    op.drop_table("route_images")
    pass
