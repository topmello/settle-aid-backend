from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, oauth2
import socketio
from datetime import datetime, timedelta, timezone
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

MAX_ATTEMPTS = 5
ROOM_EXPIRY_DURATION = timedelta(minutes=30)


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
            print(f'{sid}: connected')
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
async def join_room(sid, roomId):

    db_gen = get_db()
    db = next(db_gen)

    # Fetch the room from the database
    room_query = db.query(models.TrackRoom).filter(
        models.TrackRoom.room_id == roomId)
    room = room_query.first()
    if not room:
        await sio_server.emit('error_message', 'Room not found', room=sid)
        return

    # Check if the room has expired
    now_utc = datetime.now(timezone.utc)
    if now_utc - room.created_at > ROOM_EXPIRY_DURATION:
        db.delete(room)
        db.commit()
        await sio_server.emit('error_message', 'Room has expired', room=sid)
        return

    # If the room is valid, let the user join
    if room:
        sio_server.enter_room(sid, roomId)
        await sio_server.emit('room_message', f'User {sid} has joined the room!', room=roomId)
    else:
        # Increment the failed attempts for this room
        room.failed_attempts += 1
        db.commit()

        # If failed attempts exceed the max limit, delete the room
        if room.failed_attempts >= MAX_ATTEMPTS:
            db.delete(room)
            db.commit()
            await sio_server.emit('error_message', 'Too many incorrect attempts. Room has been removed.', room=sid)
        else:
            await sio_server.emit('error_message', 'Incorrect room ID provided', room=sid)

    # Close the DB session
    next(db_gen, None)


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
