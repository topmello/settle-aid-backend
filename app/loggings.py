from fastapi import Request, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Union
import aioredis
import asyncio
import json
from datetime import datetime

from .redis import get_redis_logs_db, redis_logs_db_context
from .common import get_log_category, LOGS_CATEGORIES, templates

LOGS_PREFIX = "logs"


class LoggingMiddleware:
    async def __call__(self, request: Request, call_next):

        response = await call_next(request)

        status_code = response.status_code

        if status_code < 400 or status_code >= 500:

            async with redis_logs_db_context() as redis_logger:

                log_message = f"{request.method} request to {request.url.path}: {status_code}"
                await log_to_redis(
                    get_log_category(request.url.path),
                    log_message,
                    redis_logger)
                return response
        else:
            return response


async def log_to_redis(category: str, message: str, r: aioredis.Redis):
    log_data = {
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "category": category
    }

    try:
        await r.xadd(f"{LOGS_PREFIX}:{category}", log_data)
    except Exception as e:
        print(f"Error logging to Redis: {e}")

    await r.xtrim(f"logs:{category}", maxlen=100, approximate=False)


async def get_logs_from_redis(category: str, r: aioredis.Redis, count=100):
    try:
        entries = await r.xrevrange(f"{LOGS_PREFIX}:{category}", count=count)
    except aioredis.exceptions.ResponseError as e:
        if "WRONGTYPE" in str(e):
            await r.delete(f"logs:{category}")
            return []  # Return an empty list if the stream doesn't exist
        raise

    logs = []
    for entry in entries:
        log_data = {
            "id": entry[0],
            "message": entry[1].get("message"),
            "timestamp": entry[1].get("timestamp"),
            "category": entry[1].get("category")
        }
        logs.append(log_data)

    return logs


async def log_exception(request: Request, exc: Union[HTTPException, RequestValidationError, RateLimitExceeded], custom_message: Optional[str] = None):
    try:
        async with redis_logs_db_context() as redis_logger:
            # Use custom_message if provided
            if custom_message:
                log_message = custom_message
            else:
                log_message = f"{request.method} request to {request.url.path}: {exc.status_code} - {exc.detail['type']} - {exc.detail['msg']}"

            await log_to_redis(
                get_log_category(request.url.path),
                log_message,
                redis_logger)
    except Exception as e:
        print(f"Error logging to Redis: {e}")


"""
API endpoints for logs
"""


async def get_logs_ui_(request: Request, r: aioredis.Redis = Depends(get_redis_logs_db)):

    logs_by_category = {}

    for category in LOGS_CATEGORIES:
        logs_by_category[category] = await get_logs_from_redis(category, r)

    return templates.TemplateResponse("logs.html", {"request": request, "logs": logs_by_category})


async def logs_stream_(r: aioredis.Redis = Depends(get_redis_logs_db)):
    logs_category = [f"logs:{category}" for category in LOGS_CATEGORIES]

    async def event_stream():
        inactive_time = 0
        while True:
            # Initialize the streams dictionary
            streams_dict = {stream: "$" for stream in logs_category}

            # Wait for log entries starting from the current ID
            entries = await r.xread(streams_dict, count=1, block=10000)
            if not entries:
                yield 'data: {"message": "ping"}\n\n'
                await asyncio.sleep(1)
                inactive_time += 1

                if inactive_time >= 3:
                    break

                continue

            for _, items in entries:
                for id, log_data in items:
                    current_id = id  # Update the current ID
                    print(json.dumps(log_data))
                    yield f"id: {id}\ndata: {json.dumps(log_data)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
