from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import aioredis
from ..database import get_db
from .. import models, schemas, oauth2
from ..redis import redis_refresh_token_db_context, redis_room_db_context, redis_logs_db_context
from ..loggings import log_to_redis

import socketio
from datetime import datetime, timedelta, timezone
import random

# Create a Socket.IO server
sio_server = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[]
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
        await sio_server.emit('error', {
            "details": {
                'type': 'invalid_credentials',
                'msg': 'Invalid credentials'
            }
        }, room=sid)
        async with redis_logs_db_context() as redis_logger:
            await log_to_redis("Track", "invalid_credentials", redis_logger)
        await sio_server.disconnect(sid)
        return

    db_gen = get_db()
    db = next(db_gen)

    try:
        token_data = await oauth2.verify_access_token(token)

        async with redis_refresh_token_db_context() as r:
            current_user = await oauth2.get_user(token_data.username, db, r)

        if current_user:
            async with redis_room_db_context() as redis_room:
                await redis_room.setex(f"userSid:{sid}", 30 * 60, current_user.username)

            async with redis_logs_db_context() as redis_logger:
                await log_to_redis("Track", f"{current_user.username} connected", redis_logger)
        else:
            async with redis_logs_db_context() as redis_logger:
                await log_to_redis("Track", "user_not_found", redis_logger)

            await sio_server.disconnect(sid)

    except HTTPException as e:
        await sio_server.emit('error', {
            "details": {
                'type': e.detail.get('type'),
                'msg': e.detail.get('msg')
            }
        }, room=sid)
        async with redis_logs_db_context() as redis_logger:
            await log_to_redis("Track", f"invalid_credentials {e.detail}", redis_logger)
        await sio_server.disconnect(sid)

    finally:
        # Close the DB session
        next(db_gen, None)


@sio_server.event
async def join_room(sid, roomId):
    async with redis_room_db_context() as redis_room:
        username = await redis_room.get(f"userSid:{sid}")

    async with redis_room_db_context() as redis_room:
        room_exists = await redis_room.exists(f"roomId:{roomId}")

    if not room_exists:
        async with redis_logs_db_context() as redis_logger:
            await log_to_redis("Track", f"no_room - roomId {roomId}", redis_logger)

        await sio_server.emit('error', {
            "details": {
                'type': 'no_room',
                'msg': 'Room not found or has expired'
            }
        }, room=sid)
        return

    # If the room is valid, let the user join
    sio_server.enter_room(sid, roomId)

    await sio_server.emit('room', {
        "details": {
            "type": "joined_room",
            "msg": f"{username} has joined room {roomId}"
        }
    }, room=roomId)
    async with redis_logs_db_context() as redis_logger:
        await log_to_redis("Track", f"{username} has joined room {roomId}", redis_logger)


@sio_server.event
async def leave_room(sid, roomId):

    async with redis_room_db_context() as redis_room:
        username = await redis_room.get(f"userSid:{sid}")

    # Remove the client from the specified room
    sio_server.leave_room(sid, roomId)

    # Notify the room that the client has left
    await sio_server.emit('room', {
        "details": {
            'type': 'lefted_room',
            'msg': f"{username} has left room {roomId}"
        }
    }, room=roomId)
    async with redis_logs_db_context() as redis_logger:
        await log_to_redis("Track", f"{username} has left room {roomId}", redis_logger)


@sio_server.event
async def move(sid, data):
    # Extract roomId, lat, and long from the data
    roomId = data.get('roomId')
    lat = data.get('lat')
    long = data.get('long')

    if roomId and lat and long:
        await sio_server.emit('move', {
            "details": {
                "type": "success",
                "msg": {'lat': lat, 'long': long}
            }
        },
            room=str(roomId))
    else:
        await sio_server.emit('error', {
            'details': {
                'type': 'invalid_data',
                'msg': 'Invalid data'
            }
        }, room=sid)


@sio_server.event
async def disconnect(sid):
    async with redis_room_db_context() as redis_room:
        username = await redis_room.get(f"userSid:{sid}")

    await sio_server.emit('room', {
        "details": {
            'type': 'disconnected',
            'msg': f"{username} disconnected"
        }
    }, room=username)

    async with redis_room_db_context() as redis_room:
        await redis_room.delete(f"userSid:{sid}")

    await sio_server.disconnect(sid)
    async with redis_logs_db_context() as redis_logger:
        await log_to_redis("Track", f"{username} disconnected", redis_logger)
