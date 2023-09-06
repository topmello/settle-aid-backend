from fastapi import APIRouter, Depends, HTTPException, WebSocket

from sqlalchemy.orm import Session

from ..database import get_db

from .. import models, schemas, oauth2

router = APIRouter(
    prefix="/track",
    tags=["Track Socket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
