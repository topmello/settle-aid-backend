
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import aioredis

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .routers import auth, user, search, translate, track_sio, track, vote, route
from .limiter import limiter

from fastapi.exceptions import RequestValidationError
from .exceptions import *
from .exception_handlers import custom_exception_handler, ratelimit_exception_handler, validation_exception_handler

from .loggings import LoggingMiddleware, get_logs_ui_, logs_stream_, get_redis_logs_db
from .common import templates, get_current_username_doc

description = """
## Logs 📜
Please go to /logs/ to view the logs.

## HTTP Exceptions 🚨
| Exception Type               | Status Code | Type                      | Message                                                                          |
| ---------------------------- | ----------- | ------------------------- | -------------------------------------------------------------------------------- |
| CustomHTTPException          | 400         | `default_type`            | DefaultMessage                                                                   |
| InvalidCredentialsException  | 401         | `invalid_credentials`     | Invalid credentials                                                              |
| UserNotFoundException        | 404         | `user_not_found`          | User not found                                                                   |
| UserAlreadyExistsException   | 400         | `user_already_exists`     | User already exists                                                              |
| InvalidRefreshTokenException | 404         | `invalid_refresh_token`   | Invalid refresh token                                                            |
| NotAuthorisedException       | 403         | `not_authorised`          | Not authorised                                                                   |
| LocationNotFoundException    | 404         | `no_location`             | Not found any location in the given area                                         |
| InvalidSearchQueryException  | 400         | `invalid_search_query`    | Invalid search query                                                             |
| RouteNotFoundException       | 404         | `no_route`                | Not found any route in the given area                                            |
| ParametersTooLargeException  | 400         | `parameters_too_large`    | Parameters too large                                                             |
| AlreadyVotedException        | 409         | `already_voted`           | Already voted                                                                    |
| VoteNotFoundException        | 404         | `vote_not_found`          | Vote not found                                                                   |
| RequestValidationError       | 400         | `missing`                 | Field required                                                                   |
| RequestValidationError       | 400         | `string_pattern_mismatch` | String should match pattern                                                      |
| RequestValidationError       | 400         | `json_invalid`            | JSON decode error                                                                |
| RequestValidationError       | 400         | `string_type`             | Input should be a valid string                                                   |
| RequestValidationError       | 400         | `string_too_short`        | String should have at least {} characters                                        |
| RequestValidationError       | 400         | `string_too_long`         | String should have at most {} characters                                         |
| RequestValidationError       | 400         | `value_error`             | Location type must be one of 'landmark', 'restaurant', 'grocery', or 'pharmacy'. |
| RequestValidationError       | 400         | `value_error`             | Route type must be one of 'driving', 'walking', or 'cycling'.                    |



## SocketIO messages 📨

| Event        | Message Type   | Details Type      | Details Msg                                    |
|--------------|----------------|-------------------|------------------------------------------------|
| `connect`    | `error`        | `invalid_credentials` | 'Invalid credentials'                      |
|              | N/A            | Varies with `HTTPException` | Depends on the error detail from exception |
| `join_room`  | `error`         | `no_room`            | 'Room not found or has expired'                |
|              | `room`         | `joined_room`        | E.g. "admin has joined room 448408"            |
| `leave_room` | `room`         | `lefted_room`        | E.g. "admin has left room 448408"              |
| `move`       | `move`         | `success`            | Object with `lat` and `long`, e.g. `{lat: 34, long: 34}` |
|              | `error`        | `invalid_data`       | 'Invalid data'                                  |
| `disconnect` | `room`         | `disconnected`       | E.g. "admin disconnected"                       |

For documentation for SocketIO connection, please refer to the [Topmello documentation](https://topmello.github.io/docs/backend/tracker).


"""

# Create FastAPI instance
app = FastAPI(
    title="Settle Aid 🚠",
    description=description,
    version="0.2.0",
    contact={
        "name": "Top Mello",
        "url": "https://topmello.github.io/"
    },
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(search.router)
app.include_router(translate.router)
app.include_router(vote.router)
app.include_router(route.router)
app.include_router(track.router)
app.mount("/track-sio", track_sio.subapi)

app.middleware("http")(LoggingMiddleware())

exceptions_to_handle = [
    InvalidCredentialsException,
    UserNotFoundException,
    InvalidRefreshTokenException,
    UserAlreadyExistsException,
    NotAuthorisedException,
    LocationNotFoundException,
    InvalidSearchQueryException,
    RouteNotFoundException,
    ParametersTooLargeException,
    AlreadyVotedException,
    VoteNotFoundException,
]

for exception in exceptions_to_handle:
    app.add_exception_handler(exception, custom_exception_handler)

app.add_exception_handler(RateLimitExceeded, ratelimit_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.on_event("startup")
async def startup_event():
    """Startup event"""
    print("Starting up...")
    prompt = "Hello World"
    embed = search.model.encode([prompt])
    pass


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


@app.get("/logs", include_in_schema=False)
async def get_logs_ui(request: Request, r: aioredis.Redis = Depends(get_redis_logs_db), username: str = Depends(get_current_username_doc)):
    return await get_logs_ui_(request, r)


@app.get("/logs/stream/", include_in_schema=False)
async def logs_stream(r: aioredis.Redis = Depends(get_redis_logs_db), username: str = Depends(get_current_username_doc)):
    return await logs_stream_(r)
