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
    log_id = f"log:{datetime.utcnow().isoformat()}"

    # Store the log details as a hash
    await r.hset(log_id, mapping={
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "category": category
    })

    # Push the log message to the beginning of the list specific to the category
    await r.lpush(f"logs:{category}", log_id)

    # Trim the list to only keep the most recent 100 entries
    await r.ltrim(f"logs:{category}", 0, 99)


async def get_logs_from_redis(category: str, r: aioredis.Redis):
    log_ids = await r.lrange(f"logs:{category}", 0, -1)

    logs = []
    for log_id in log_ids:
        log_data = await r.hgetall(log_id)
        logs.append(log_data)

    return logs


redis_url_limiter = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOSTNAME}:{settings.REDIS_PORT}/15"
