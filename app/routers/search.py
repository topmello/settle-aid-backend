from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from sentence_transformers import SentenceTransformer

from ..database import get_db

from .. import models, schemas, oauth2

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}},
)

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

@router.get("/")
async def search_by_prompt(db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    query_embeding = model.encode(["Hello world"])[0]
    print(query_embeding.shape)
    query = db.query(models.Landmark).limit(10)
    print(query.all())

    # Place holder for now
    return {"message": "Get result"}