import redis
from .config import settings

redis_refresh_token_db = redis.Redis(
    host=settings.REDIS_HOSTNAME,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=0,
    decode_responses=True)

redis_room_db = redis.Redis(
    host=settings.REDIS_HOSTNAME,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=14)

redis_url_limiter = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOSTNAME}:{settings.REDIS_PORT}/15"
