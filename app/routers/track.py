from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, oauth2
from ..limiter import rate_limited_route

import random

router = APIRouter(
    prefix="/track",
    tags=["Track"],
    responses={404: {"description": "Not found"}},
)


@router.get("/generate-pin/", response_model=schemas.TrackRoomOut)
async def test(db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user), _rate_limited: bool = Depends(rate_limited_route)):
    room_id = str(random.randint(1000, 9999))
    pin = str(random.randint(1000, 9999))

    insert_db = models.TrackRoom(
        room_id=room_id, user_id=current_user.user_id, pin=pin)
    db.add(insert_db)
    db.commit()

    return schemas.TrackRoomOut(room_id=room_id, pin=pin)
