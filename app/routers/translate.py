from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from .. import models, schemas, oauth2, translation

import aioredis
from ..redis import get_redis_logs_db, log_to_redis

router = APIRouter(
    prefix="/translate",
    tags=["Translate"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=schemas.TranslateRes)
async def translate(
        request: Request,
        query: schemas.TranslateQuery,
        r_logger: aioredis.Redis = Depends(get_redis_logs_db)):

    await log_to_redis("Translate", f"{request.method} request to {request.url.path}", r_logger)

    translate_text = translation.translate_list(query.texts)

    await log_to_redis("Translate", f"Translated {query.texts}", r_logger)

    return schemas.TranslateRes(results=translate_text)
