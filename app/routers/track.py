from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, oauth2
from ..redis import redis_room_db
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
async def generate_room_pin(request: Request, db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    room_id = str(random.randint(100000, 999999))
    redis_room_db.setex(room_id, ROOM_EXPIRY_DURATION, 'active')

    return schemas.TrackRoomOut(room_id=room_id)
