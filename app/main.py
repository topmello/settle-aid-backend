from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

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

description = """
# Authentication 🔑

- Login to the API to get an access token.

# User 👩‍🦳

- Generate a random username.
- Get user information.
- Create a new user.


# Search Route 🛵
- Generate route given list of prompts and locations

# Translate 🇦🇺
- Implemented using Google Translate API

# Track 🛤️
- WebSocket connection to track a user's location

To be continue ...
"""
# Create FastAPI instance
app = FastAPI(
    title="Settle Aid 🚠",
    description=description,
    version="0.1.0",
    contact={
        "name": "Top Mello",
        "url": "https://topmello.github.io/"
    },
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

security = HTTPBasic()

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


def get_current_username_doc(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(
        credentials.username, settings.DOC_USERNAME)
    correct_password = secrets.compare_digest(
        credentials.password, settings.DOC_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/", include_in_schema=False)
async def get_swagger_documentation(username: str = Depends(get_current_username_doc)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@app.get("/openapi.json", include_in_schema=False)
async def openapi(username: str = Depends(get_current_username_doc)):
    return get_openapi(
        title=app.title,
        description=app.description,
        contact=app.contact,
        version=app.version,
        routes=app.routes)
