"""create prompt_route and backfill

Revision ID: 1e9aeac89c4a
Revises: ffd40eb69bae
Create Date: 2023-10-07 09:31:56.018876

"""
from alembic import op
import sqlalchemy as sa
from app.database import get_db
from app import models

# revision identifiers, used by Alembic.
revision = '1e9aeac89c4a'
down_revision = 'ffd40eb69bae'
branch_labels = None
depends_on = None


def upgrade() -> None:
    models.Prompt_Route.__table__.create(op.get_bind())

    op.execute("COMMIT")
    db = next(get_db())
    for prompt in db.query(models.Prompt).all():
        route = db.query(models.Route).filter(
            models.Route.created_by_user_id == prompt.created_by_user_id,
            models.Route.created_at == prompt.created_at
        ).first()

        if route:
            prompt_route = models.Prompt_Route(
                prompt_id=prompt.prompt_id,
                created_by_user_id=prompt.created_by_user_id,
                route_id=route.route_id
            )
            db.add(prompt_route)
            db.commit()

    pass


def downgrade() -> None:
    models.Prompt_Route.__table__.drop(op.get_bind())
    pass
