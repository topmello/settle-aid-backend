from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from .. import models, schemas, oauth2, translation


router = APIRouter(
    prefix="/translate",
    tags=["Translate"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=schemas.TranslateRes)
async def translate(
        request: Request,
        query: schemas.TranslateQuery):

    translate_text = translation.translate_list(query.texts)

    return schemas.TranslateRes(results=translate_text)
