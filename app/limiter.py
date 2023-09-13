from slowapi import Limiter
from slowapi.util import get_remote_address
from .redis import redis_url_limiter


limiter = Limiter(key_func=get_remote_address, storage_uri=redis_url_limiter)
