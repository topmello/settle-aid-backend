import aioredis
from .config import settings

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


@asynccontextmanager
async def redis_refresh_token_db_context():
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


redis_url_limiter = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOSTNAME}:{settings.REDIS_PORT}/15"
