from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

router = APIRouter(
    prefix='/challenge',
    tags=["Challenge"]
)


@router.get("/")
async def get_challenge():
    return {"message": "Hello World"}
