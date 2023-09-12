from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, oauth2
import socketio

import random


sio_server = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[],
    logger=True,
    engineio_logger=True
)

sio_app = socketio.ASGIApp(sio_server, socketio_path="sio")

subapi = FastAPI()
subapi.mount("/", sio_app)

"""
@sio_server.event
async def connect(sid, environ, auth):
    print(f'{sid}: connected')
    await sio_server.emit('join', {'sid': sid})
"""


@sio_server.event
async def connect(sid, environ):
    # Extract the token from the environ object
    token = environ.get("HTTP_AUTHORIZATION")
    if token and token.startswith("Bearer "):
        token = token[7:]  # Remove the "Bearer " prefix

    # If there's no token, disconnect the user
    if not token:
        print("No token provided")
        await sio_server.disconnect(sid)
        return

    db_gen = get_db()
    db = next(db_gen)

    try:
        # Verify the token
        credentials_exception = HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        token_data = oauth2.verify_access_token(token, credentials_exception)
        user_query = db.query(models.User).filter(
            models.User.user_id == token_data.user_id)
        current_user = user_query.first()

        if current_user:
            user_id = current_user.user_id
            sio_server.enter_room(sid, str(user_id))

            pin = 1234  # str(random.randint(1000, 9999))

            await sio_server.emit('your_pin', pin, room=str(user_id))
        else:
            print("User not found")
            await sio_server.disconnect(sid)

    except HTTPException as e:
        print(f"Token verification failed: {e.detail}")
        await sio_server.disconnect(sid)

    finally:
        # Close the DB session
        next(db_gen, None)


@sio_server.event
async def join_room(sid, data):
    roomId = data.get('roomId')
    pin = data.get('pin')

    # Check if the provided pin matches the room pin
    if str(1234) == pin:
        sio_server.enter_room(sid, roomId)
        await sio_server.emit('room_message', f'User {sid} has joined the room!', room=roomId)
    else:
        await sio_server.emit('error_message', 'Incorrect pin provided', room=sid)


@sio_server.event
async def leave_room(sid, roomId):
    # Remove the client from the specified room
    sio_server.leave_room(sid, roomId)

    # Notify the room that the client has left
    await sio_server.emit('room_message', f'User {sid} has left the room!', room=roomId)


@sio_server.event
async def move(sid, data):
    # Extract roomId, lat, and long from the data
    roomId = data.get('roomId')
    lat = data.get('lat')
    long = data.get('long')

    if roomId and lat and long:
        await sio_server.emit('move', {'sid': sid, 'lat': lat, 'long': long}, room=str(roomId))
    else:
        print("Incomplete data provided in move event")


@sio_server.event
async def disconnect(sid):
    print(f'{sid}: disconnected')
    await sio_server.disconnect(sid)
