from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import aioredis
from ..database import get_db
from .. import models, schemas, oauth2
from ..redis import redis_room_db_context, redis_logs_db_context, log_to_redis
import socketio
from datetime import datetime, timedelta, timezone
import random

# Create a Socket.IO server
sio_server = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[],
    logger=True,
    engineio_logger=True
)

sio_app = socketio.ASGIApp(sio_server, socketio_path="sio")

subapi = FastAPI()
subapi.mount("/", sio_app)


@sio_server.event
async def connect(sid, environ):

    # Extract the token from the environ object
    token = environ.get("HTTP_AUTHORIZATION")
    if token and token.startswith("Bearer "):
        token = token[7:]  # Remove the "Bearer " prefix

    # If there's no token, disconnect the user
    if not token:
        async with redis_logs_db_context() as redis_logger:
            await log_to_redis("Track", f"Token not provided", redis_logger)
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
        token_data = await oauth2.verify_access_token(token, credentials_exception)
        user_query = db.query(models.User).filter(
            models.User.user_id == token_data.user_id)
        current_user = user_query.first()

        if current_user:
            async with redis_logs_db_context() as redis_logger:
                await log_to_redis("Track", f"User {current_user.user_id} with Sid {sid} connected", redis_logger)
            print(f'{sid}: connected')
        else:
            async with redis_logs_db_context() as redis_logger:
                await log_to_redis("Track", f"User not found", redis_logger)
            print("User not found")
            await sio_server.disconnect(sid)

    except HTTPException as e:
        async with redis_logs_db_context() as redis_logger:
            await log_to_redis("Track", f"Token verification failed: {e.detail}", redis_logger)
        print(f"Token verification failed: {e.detail}")
        await sio_server.disconnect(sid)

    finally:
        # Close the DB session
        next(db_gen, None)


@sio_server.event
async def join_room(sid, roomId):

    async with redis_room_db_context() as redis_room:
        room_exists = await redis_room.exists(roomId)

    if not room_exists:
        async with redis_logs_db_context() as redis_logger:
            await log_to_redis("Track", f"Room not found or has expired", redis_logger)

        await sio_server.emit('error_message', 'Room not found or has expired', room=sid)
        return

    # If the room is valid, let the user join
    sio_server.enter_room(sid, roomId)

    await sio_server.emit('room_message', f'User {sid} has joined the room!', room=roomId)
    async with redis_logs_db_context() as redis_logger:
        await log_to_redis("Track", f"Sid {sid} has joined room {roomId}", redis_logger)


@sio_server.event
async def leave_room(sid, roomId):

    # Remove the client from the specified room
    sio_server.leave_room(sid, roomId)

    # Notify the room that the client has left
    await sio_server.emit('room_message', f'User {sid} has left the room!', room=roomId)
    async with redis_logs_db_context() as redis_logger:
        await log_to_redis("Track", f"Sid {sid} has left room {roomId}", redis_logger)


@sio_server.event
async def move(sid, data):
    # Extract roomId, lat, and long from the data
    roomId = data.get('roomId')
    lat = data.get('lat')
    long = data.get('long')

    if roomId and lat and long:
        await sio_server.emit('move', {'sid': sid, 'lat': lat, 'long': long}, room=str(roomId))
    else:
        await sio_server.emit('error_message', 'Incomplete data provided in move event', room=sid)


@sio_server.event
async def disconnect(sid):

    print(f'{sid}: disconnected')
    await sio_server.disconnect(sid)
    async with redis_logs_db_context() as redis_logger:
        await log_to_redis("Track", f"Sid {sid} disconnected", redis_logger)
