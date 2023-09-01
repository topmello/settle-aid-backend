from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from .. import models, schemas, oauth2, translation

router = APIRouter(
    prefix="/translate",
    tags=["Translate"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=schemas.TranslateRes)
def translate(query: schemas.TranslateQuery):
    return schemas.TranslateRes(result=translation.translate_text(query.query, query.language))
