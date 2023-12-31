from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
import aioredis
from ..database import get_db
from .. import models, schemas, oauth2
from ..redis import get_redis_room_db
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
        redis_room_db: aioredis.Redis = Depends(get_redis_room_db)):
    """
    Generate a unique room PIN and store it in Redis with an expiry.

    Args:
    - Logged in required: The user must be logged in to generate a room PIN.

    Raises:
    - None: This function does not explicitly raise any exceptions, but dependencies may raise exceptions if any issues occur.

    Returns:
    - schemas.TrackRoomOut: The generated room PIN.

    Note:
    - The generated room PIN is stored in Redis with 30 minutes expiry duration.
    """

    room_id = str(random.randint(100000, 999999))
    await redis_room_db.setex(f"roomId:{room_id}", ROOM_EXPIRY_DURATION, 'active')

    return schemas.TrackRoomOut(room_id=room_id)
