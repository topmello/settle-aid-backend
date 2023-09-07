from fastapi import Request, HTTPException, Depends
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def get_limiter(request: Request):
    return request.app.state.limiter


def rate_limit_request(request: Request):
    # This function will be decorated and will handle the actual rate limiting.
    pass


@limiter.limit("2/second")
def rate_limited_route(request: Request, limiter_instance: Limiter = Depends(get_limiter)):
    try:
        rate_limit_request(request)
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    return True


