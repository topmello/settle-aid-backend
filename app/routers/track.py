from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from sqlalchemy.orm import Session


from ..database import get_db

from .. import models, schemas, oauth2

from ..websocket import ws_manager

router = APIRouter(
    prefix="/track",
    tags=["Track Socket"])


@router.websocket("/ws/{sender_id}/to/{receiver_id}")
async def ws_track(websocket: WebSocket, sender_id: int, receiver_id: int):

    await websocket.accept()
    await ws_manager.connect(sender_id, receiver_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.send_message(sender_id, receiver_id, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(sender_id, receiver_id, websocket)
        await websocket.close()
