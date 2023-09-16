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
    """
    Translate a list of texts based on the provided query.

    Args:
    - query (schemas.TranslateQuery): The translation query containing the list of texts to be translated.

    Raises:
    - None: This function does not explicitly raise any exceptions, but internal methods or dependencies might raise exceptions if any issues occur.

    Returns:
    - schemas.TranslateRes: The translated results corresponding to the input texts.

    """

    translate_text = translation.translate_list(query.texts)

    return schemas.TranslateRes(results=translate_text)
