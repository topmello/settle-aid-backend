import aioredis
from .config import settings
from datetime import datetime
from contextlib import asynccontextmanager


async def get_redis_refresh_token_db():
    redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOSTNAME}:{settings.REDIS_PORT}/0"
    redis = aioredis.from_url(
        redis_url, encoding='utf-8', decode_responses=True)
    conn = redis.client()
    try:
        yield conn
    finally:
        await conn.close()


async def get_redis_room_db():
    redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOSTNAME}:{settings.REDIS_PORT}/1"
    redis = aioredis.from_url(
        redis_url, encoding='utf-8', decode_responses=True)
    conn = redis.client()
    try:
        yield conn
    finally:
        await conn.close()


@asynccontextmanager
async def redis_room_db_context():
    redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOSTNAME}:{settings.REDIS_PORT}/1"
    redis = aioredis.from_url(
        redis_url, encoding='utf-8', decode_responses=True)
    conn = redis.client()
    try:
        yield conn
    finally:
        await conn.close()


async def get_redis_logs_db():
    redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOSTNAME}:{settings.REDIS_PORT}/14"
    redis = aioredis.from_url(
        redis_url, encoding='utf-8', decode_responses=True)
    conn = redis.client()
    try:
        yield conn
    finally:
        await conn.close()


@asynccontextmanager
async def redis_logs_db_context():
    redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOSTNAME}:{settings.REDIS_PORT}/14"
    redis = aioredis.from_url(
        redis_url, encoding='utf-8', decode_responses=True)
    conn = redis.client()
    try:
        yield conn
    finally:
        await conn.close()


async def log_to_redis(category: str, message: str, r: aioredis.Redis):
    log_data = {
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "category": category
    }

    try:
        await r.xadd(f"logs:{category}", log_data)
    except Exception as e:
        print(f"Error logging to Redis: {e}")

    await r.xtrim(f"logs:{category}", maxlen=100, approximate=False)


async def get_logs_from_redis(category: str, r: aioredis.Redis, count=100):
    try:
        entries = await r.xrevrange(f"logs:{category}", count=count)
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


redis_url_limiter = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOSTNAME}:{settings.REDIS_PORT}/15"
