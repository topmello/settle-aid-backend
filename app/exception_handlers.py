from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .exceptions import CustomHTTPException
from .loggings import log_exception


async def custom_exception_handler(
        request: Request,
        exc: CustomHTTPException):

    await log_exception(request, exc)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "details": {
                "type": exc.detail["type"],
                "msg": exc.detail["msg"]
            }
        },
    )


async def ratelimit_exception_handler(request: Request, exc: RateLimitExceeded):
    custom_msg = f"{request.method} request to {request.url.path}: 429 - rate_limit_exceeded - Rate limit exceeded for IP: {get_remote_address(request)}"
    await log_exception(request, exc, custom_msg)

    return JSONResponse(content={"detail": {
        "type": "rate_limit_exceeded",
        "msg": "Rate limit exceeded"
    }}, status_code=429)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    if len(errors) == 1:
        error = errors[0]
        error_type = error.get("type", "unknown")
        error_msg = error.get("msg", "An error occurred")

        custom_msg = f"{request.method} request to {request.url.path}: 400 - {error_type} - {error_msg}"
        await log_exception(request, exc, custom_msg)

        return JSONResponse(status_code=400, content={"detail": {
            "type": error_type,
            "msg": error_msg
        }})
    else:
        extracted_errors = [{"type": error.get("type", "unknown"), "msg": error.get(
            "msg", "An error occurred")} for error in errors]

        custom_msg = f"{request.method} request to {request.url.path}: 400 - {extracted_errors}"
        await log_exception(request, exc, custom_msg)

        return JSONResponse(status_code=400, content={"detail": extracted_errors})
