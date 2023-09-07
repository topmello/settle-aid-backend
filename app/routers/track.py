from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, oauth2
import socketio

sio_server = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[],
)

sio_app = socketio.ASGIApp(sio_server, socketio_path="sio")

subapi = FastAPI()
subapi.mount("/", sio_app)


@sio_server.event
async def connect(sid, environ, auth):
    print(f'{sid}: connected')
    await sio_server.emit('join', {'sid': sid})


@sio_server.event
async def chat(sid, message):
    await sio_server.emit('chat', {'sid': sid, 'message': message})


@sio_server.event
async def disconnect(sid):
    print(f'{sid}: disconnected')


@sio_server.event
async def connect_(sid, environ):
    # Extract the token from the environ object
    token = environ.get("HTTP_AUTHORIZATION")
    if token and token.startswith("Bearer "):
        token = token[7:]  # Remove the "Bearer " prefix

    # If there's no token, disconnect the user or handle this case differently
    if not token:
        print("No token provided")
        await sio_server.disconnect(sid)
        return

    # Use your existing functions to verify the token and get the user
    try:
        current_user = get_current_user(token)
        if current_user:
            user_id = current_user.user_id
            sio.enter_room(sid, str(user_id))
        else:
            print("User not found")
            await sio_server.disconnect(sid)
    except HTTPException as e:
        print(f"Token verification failed: {e.detail}")
        await sio_server.disconnect(sid)


@sio_server.event
async def create_room(sid, data):
    user_id = data["user_id"]
    room_name = f"room_{user_id}"
    sio.enter_room(sid, room_name)
    print(f"User {user_id} created room {room_name}")


@sio_server.event
async def join_room(sid, data):
    creator_user_id = data["creator_user_id"]
    room_name = f"room_{creator_user_id}"
    sio.enter_room(sid, room_name)
    print(f"User joined room {room_name}")


@sio_server.event
async def private_message(sid, data):
    # data should contain the recipient's user_id and the message
    recipient_id = data["recipient_id"]
    message = data["message"]

    await sio.emit("private_message", {"message": message}, room=str(recipient_id))
