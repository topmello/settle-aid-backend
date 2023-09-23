from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

router = APIRouter(
    prefix='/challange',
    tags=["Challange"]
)


@route.get("/")
async def get_challange():
    return {"message": "Hello World"}
