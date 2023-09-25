from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from .. import schemas, models, oauth2
from ..database import get_db


router = APIRouter(
    prefix='/challenge',
    tags=["Challenge"]
)


@router.get("/")
async def get_challenge(db: Session = Depends(get_db)):
    query = db.query(models.Challenge).all()
    return query
