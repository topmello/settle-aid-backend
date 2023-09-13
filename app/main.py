from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import redis

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from sqlalchemy.orm import Session

from .config import settings
from .routers import auth, user, search, translate, track_sio, track, vote, route
from .database import get_db
from . import models
from .limiter import limiter

import json


description = """
# Authentication 🔑

- Login Endpoint (/login): Authenticates the user and returns a JWT token. If the user exceeds the maximum allowed login attempts, their IP is blocked for a specified duration.
- Login V2 Endpoint (/v2/login): An enhanced version of the login endpoint. In addition to authenticating the user and returning a JWT token, it also provides a refresh token. If a user already has a refresh token, the old one is deleted and a new one is generated.
- Refresh Token Endpoint (/v2/token/refresh): Allows the user to get a new JWT token using their refresh token. The refresh token remains the same.

# User 👩‍🦳

- Generate Username Endpoint (/generate): Generates a unique username. If the generated name exists in the database, it keeps generating until a unique name is found.
- Get User Details Endpoint (/{user_id}): Retrieves the details of a user and their history based on the provided user ID.
- Create User Endpoint (/): Creates a new user in the database.


# Search Route 🛵
- Search by Query Sequence Endpoint (/route/): Searches for a sequence of locations based on the user's queries. For each query, it finds a location that matches the query's embedding and then creates a route based on the sequence of found locations.

# Translate 🇦🇺
- Translate Endpoint (/): Translates a list of texts into the target language (English) using the Google Cloud Translation API.

# Track 🛤️
- WebSocket connection to track a user's location

To be continue ...
"""

redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

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


# Add CORS middleware need to change this later for more security
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(search.router)
app.include_router(translate.router)
app.include_router(vote.router)
app.include_router(route.router)
app.include_router(track.router)
app.mount("/track-sio", track_sio.subapi)


@app.on_event("startup")
async def startup_event():
    """Startup event"""
    print("Starting up...")
    prompt = "Hello World"
    embed = search.model.encode([prompt])
    pass


@app.get("/test")
@limiter.limit("1/second")
async def test(request: Request):
    return {"message": "Hello World"}


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
