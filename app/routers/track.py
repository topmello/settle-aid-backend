from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import aioredis
from ..database import get_db
from .. import models, schemas, oauth2
from ..redis import get_redis_room_db, get_redis_logs_db, log_to_redis
from ..limiter import limiter


import random

router = APIRouter(
    prefix="/track",
    tags=["Track"],
    responses={404: {"description": "Not found"}},
)


ROOM_EXPIRY_DURATION = 30 * 60  # 30 minutes in seconds


@router.get("/generate-pin/", response_model=schemas.TrackRoomOut)
@limiter.limit("1/second")
async def generate_room_pin(
        request: Request,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user),
        redis_room_db: aioredis.Redis = Depends(get_redis_room_db),
        r_logger: aioredis.Redis = Depends(get_redis_logs_db)):

    await log_to_redis("Track", f"{request.method} request to {request.url.path}", r_logger)

    room_id = str(random.randint(100000, 999999))
    await redis_room_db.setex(room_id, ROOM_EXPIRY_DURATION, 'active')

    await log_to_redis("Track", f"Generated room pin {room_id}", r_logger)

    return schemas.TrackRoomOut(room_id=room_id)
