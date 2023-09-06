from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from fastapi_socketio import SocketManager

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from .config import settings
from .routers import auth, user, search, translate, track
from .database import get_db
from . import models
from .limiter import limiter

import json
# Create FastAPI instance
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add SocketIO support
socket_manager = SocketManager(app=app)


# Add CORS middleware need to change this later for more security
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(search.router)
app.include_router(translate.router)
app.include_router(track.router)


@app.on_event("startup")
async def startup_event():
    """Startup event"""
    print("Starting up...")
    prompt = "Hello World"
    embed = search.model.encode([prompt])
    pass


@app.get("/")
async def root():
    return {"message": "Hello World"}
