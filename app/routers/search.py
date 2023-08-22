from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from sentence_transformers import SentenceTransformer

from ..database import get_db

from .. import models, schemas

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}},
)

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

@router.get("/")
async def search_by_prompt(db: Session = Depends(get_db)):
    query_embeding = model.encode(["Hello world"])[0]
    print(query_embeding.shape)

    # Place holder for now
    return {"message": "Get result"}