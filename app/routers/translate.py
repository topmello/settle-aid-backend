from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from ..limiter import rate_limited_route

from .. import models, schemas, oauth2, translation

router = APIRouter(
    prefix="/translate",
    tags=["Translate"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=schemas.TranslateRes)
def translate(query: schemas.TranslateQuery, _rate_limited: bool = Depends(rate_limited_route)):
    translate_text = translation.translate_list(query.texts)

    return schemas.TranslateRes(results=translate_text)
