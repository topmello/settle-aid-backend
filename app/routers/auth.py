from fastapi import APIRouter, Depends, Request, Response
from datetime import datetime
from sqlalchemy.orm import Session
import json
import aioredis
import asyncio

from ..common import templates
from ..database import get_db
from ..redis import get_redis_refresh_token_db
from ..limiter import limiter

from .. import models, schemas, oauth2
from .user import verify
from ..exceptions import InvalidCredentialsException, UserNotFoundException, InvalidRefreshTokenException


router = APIRouter(
    prefix="/login",
    tags=["Authentication"]
)


@router.post('/', response_model=schemas.Token)
@limiter.limit("5/second")
async def login(
        request: Request,
        user_credentials: schemas.LoginRequest,
        db: Session = Depends(get_db)):
    """
    Authenticate a user and return an access token.

    Args:
    - user_credentials (schemas.LoginRequest): Contains the user's username and password.

    Raises:
    - UserNotFoundException: If the specified user does not exist.
    - InvalidCredentialsException: If the password verification fails.

    Returns:
    - dict: JWT token with token type.
    """
    # user_credentials contains username and password
    user_query = db.query(models.User).filter(
        models.User.username == user_credentials.username)
    if user_query.first() is None:
        raise UserNotFoundException()
    if not verify(user_credentials.password, user_query.first().password):
        raise InvalidCredentialsException()

    # Generate JWT token
    access_token = oauth2.create_access_token(data={
        "user_id": user_query.first().user_id,
        "username": user_credentials.username
    })

    return {"access_token": access_token, "token_type": "bearer"}


async def login_(
        request: Request,
        user_credentials: schemas.LoginRequest,
        db: Session,
        r: aioredis.Redis
) -> schemas.TokenV2:
    user = await oauth2.get_user(user_credentials.username, db, r)

    if not user:
        raise UserNotFoundException()
    if not verify(user_credentials.password, user.password):
        raise InvalidCredentialsException()

    user_id = user.user_id
    # Delete existing refresh token from Redis
    await r.delete(f"refresh_token:{user_id}")

    # Generate JWT token
    access_token, access_token_expire = oauth2.create_access_token_v2(data={
        "user_id": user_id,
        "username": user_credentials.username
    })
    # Generate refresh token
    refresh_token_data = {"user_id": user_id}
    refresh_token, refresh_token_expiry = oauth2.create_refresh_token(
        data=refresh_token_data)

    # Store refresh token and its expiry in Redis as a JSON string
    token_data = {
        "token": refresh_token,
        "user_id": user_id,
        "username": user_credentials.username,
        "expires_at": refresh_token_expiry.isoformat()
    }
    ttl = (refresh_token_expiry - datetime.utcnow()).total_seconds()
    await r.setex(f"refresh_token:{user_id}", int(
        ttl), json.dumps(token_data))

    user_logged_in = schemas.TokenV2(
        user_id=user_id,
        username=user_credentials.username,
        access_token=access_token,
        token_type="bearer",
        access_token_expire=access_token_expire,
        refresh_token=refresh_token,
        refresh_token_expire=refresh_token_expiry
    )
    return user_logged_in


@router.post('/v2/', response_model=schemas.TokenV2)
@limiter.limit("5/second")
async def login(
        request: Request,
        user_credentials: schemas.LoginRequest,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_refresh_token_db)):
    """
    Authenticate a user and return an enhanced access token (v2).

    Args:
    - user_credentials (schemas.LoginRequest): Contains the user's username and password.

    Raises:
    - UserNotFoundException: If the specified user does not exist.
    - InvalidCredentialsException: If the password verification fails.

    Returns:
    - dict: JWT token, refresh token, token type, and respective expiries.
    """

    user_logged_in = await login_(request, user_credentials, db, r)

    # Check for a custom header from the web UI
    is_web_ui = request.headers.get("X-Client-Type") == "web-ui"

    if is_web_ui:
        response_content = templates.TemplateResponse(
            "welcome.html", {"request": request, "username": user_logged_in.username}).body
        # If it's a web UI request, set the JWT as a cookie
        response = Response(content=response_content, media_type="text/html")
        response.set_cookie(
            key="access_token",
            value=user_logged_in.access_token,
            httponly=True,
            max_age=3600,
            samesite="lax",
            secure=True
        )
        return response
    else:
        return user_logged_in


@router.post('/v2/refresh/', response_model=schemas.TokenV2)
@limiter.limit("5/second")
async def refresh_token(
        request: Request,
        refresh_token: schemas.RefreshTokenIn,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_refresh_token_db)):
    """
    Refresh an access token using a provided refresh token.

    Args:
    - refresh_token (schemas.RefreshTokenIn): Contains the refresh token used to generate a new access token.

    Raises:
    - InvalidRefreshTokenException: If the refresh token is invalid or has expired.

    Returns:
    - dict: New JWT token, existing refresh token, token type, and respective expiries.
    """

    # Verify the JWT signature and get the user_id
    user_id = oauth2.verify_refresh_token(refresh_token.refresh_token)

    # Retrieve the stored token data and user data (if cached) from Redis
    stored_token_data, cached_user_data = await asyncio.gather(
        r.get(f"refresh_token:{user_id}"),
        r.get(f"user_data:{user_id}")
    )

    if not stored_token_data:
        raise InvalidRefreshTokenException()

    # Parse the JSON string to get the token and its expiration time
    token_data = json.loads(stored_token_data)
    if token_data["token"] != refresh_token.refresh_token:
        raise InvalidRefreshTokenException()

    # Check if the token has expired
    if datetime.fromisoformat(token_data["expires_at"]) < datetime.utcnow():
        raise InvalidRefreshTokenException()

    user = await oauth2.get_user(token_data['username'], db, r)

    # Generate new access token
    access_token, access_token_expire = oauth2.create_access_token_v2(
        data={"user_id": user.user_id, "username": user.username})

    return {
        "user_id": user_id,
        "username": user.username,
        "access_token": access_token,
        "token_type": "bearer",
        "access_token_expire": access_token_expire,
        "refresh_token": token_data["token"],
        "refresh_token_expire": token_data["expires_at"]
    }
