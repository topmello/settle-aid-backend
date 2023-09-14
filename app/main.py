from fastapi.responses import StreamingResponse
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
import secrets
import aioredis
import asyncio
import json
import time

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
from .redis import get_redis_logs_db, redis_logs_db_context, log_to_redis, get_logs_from_redis


description = """
## Authentication 🔑

- Login Endpoint (/login): Authenticates the user and returns a JWT token. If the user exceeds the maximum allowed login attempts, their IP is blocked for a specified duration.
- Login V2 Endpoint (/v2/login): An enhanced version of the login endpoint. In addition to authenticating the user and returning a JWT token, it also provides a refresh token. If a user already has a refresh token, the old one is deleted and a new one is generated.
- Refresh Token Endpoint (/v2/token/refresh): Allows the user to get a new JWT token using their refresh token. The refresh token remains the same.

## User 👩‍🦳

- Generate Username Endpoint (/generate): Generates a unique username. If the generated name exists in the database, it keeps generating until a unique name is found.
- Get User Details Endpoint (/{user_id}): Retrieves the details of a user and their history based on the provided user ID.
- Create User Endpoint (/): Creates a new user in the database.


## Search Route 🛵
- Search by Query Sequence Endpoint (/route/): Searches for a sequence of locations based on the user's queries. For each query, it finds a location that matches the query's embedding and then creates a route based on the sequence of found locations.

## Translate 🇦🇺
- Translate Endpoint (/): Translates a list of texts into the target language (English) using the Google Cloud Translation API.

## Track 🛤️
- SocketIO connection to track a user's location
For documentation for SocketIO connection, please refer to the [Topmello documentation](https://topmello.github.io/docs/backend/tracker).

## Logs 📜
Please go to /logs/ to view the logs.

Some general HTTP status codes and guidelines:
- 401: Unauthorized: This error occurs when the user is not authenticated. The logs should be in the Auth category.
- 422: Unprocessable Entity (Validation Error): This error occurs when the request body is invalid. The logs should be in the Validation category.
- 429: Too Many Requests: This error occurs when the user exceeds the rate limit. The logs should be in the RateLimit category.

Notes:
- All the timestamps are in UTC.

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

templates = Jinja2Templates(directory="app/templates")


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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    endpoint = request.url.path
    # Log the error details
    async with redis_logs_db_context() as redis_logger:
        await log_to_redis("Validation", f"{request.method} request to {request.url.path}: {str(exc.errors())}", redis_logger)

    # Return the default FastAPI error response
    return JSONResponse(content={"detail": exc.errors()}, status_code=400)


@app.exception_handler(RateLimitExceeded)
async def ratelimit_exception(request: Request, exc: RateLimitExceeded):
    # Log the rate limit exceedance to Redis
    async with redis_logs_db_context() as redis_logger:
        await log_to_redis("RateLimit", f"Rate limit exceeded for IP: {get_remote_address(request)}", redis_logger)
    await redis_logger.close()

    # Return a custom response or the default one
    return JSONResponse(content={"detail": "Too many requests"}, status_code=429)


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


@app.get("/logs")
async def get_logs_ui(request: Request, r: aioredis.Redis = Depends(get_redis_logs_db)):
    categories = ["Auth", "Search", "Route",
                  "Track", "Translate", "User", "Vote", "Validation", "RateLimit"]
    logs_by_category = {}

    for category in categories:
        logs_by_category[category] = await get_logs_from_redis(category, r)

    return templates.TemplateResponse("logs.html", {"request": request, "logs": logs_by_category})


@app.get("/logs/stream/")
async def logs_stream(r: aioredis.Redis = Depends(get_redis_logs_db)):
    categories = ["Auth", "Search", "Route",
                  "Track", "Translate", "User", "Vote", "Validation", "RateLimit"]
    logs_category = [f"logs:{category}" for category in categories]

    async def event_stream():
        inactive_time = 0
        while True:
            # Initialize the streams dictionary
            streams_dict = {stream: "$" for stream in logs_category}

            # Wait for log entries starting from the current ID
            entries = await r.xread(streams_dict, count=1, block=10000)
            if not entries:
                await asyncio.sleep(1)
                inactive_time += 1

                if inactive_time >= 3:
                    break

                continue

            for _, items in entries:
                for id, log_data in items:
                    current_id = id  # Update the current ID
                    yield f"id: {id}\ndata: {json.dumps(log_data)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
