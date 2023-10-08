from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json

from .config import settings
from .schemas import TokenData, User
from .database import get_db
from . import models
import aioredis
from .redis import get_redis_refresh_token_db
from .exceptions import (
    InvalidCredentialsException,
    UserNotFoundException,
    InvalidRefreshTokenException
)


class CustomOAuth2PasswordBearer(OAuth2PasswordBearer):
    def __init__(self, tokenUrl, **kwargs):
        super().__init__(tokenUrl, **kwargs)

    async def __call__(self, request: Request):

        authorization: str = request.headers.get("Authorization")
        cookie_token: str = request.cookies.get("access_token")
        if authorization and authorization.startswith("Bearer"):
            token = authorization.split("Bearer ")[-1].strip()
            if not token:
                raise InvalidCredentialsException()
            return token

        elif cookie_token:
            return cookie_token

        else:
            raise InvalidCredentialsException()


oauth2_scheme = CustomOAuth2PasswordBearer(tokenUrl="login/form/")


async def get_user(
    username: str,
    db: Session = Depends(get_db),
    r: aioredis.Redis = Depends(get_redis_refresh_token_db)
):

    # Check if user data is in Redis cache
    cached_user_data = await r.get(f"user_data:{username}")

    if cached_user_data != "null" and cached_user_data is not None:
        user = json.loads(cached_user_data)
        user = User(**user)

    else:
        user = db.query(models.User).filter(
            models.User.username == username).first()

        if not user:
            raise UserNotFoundException()

        user = User(**user.__dict__)
        # Cache the user data in Redis for future requests
        await r.setex(
            f"user_data:{username}",
            settings.USER_CACHE_EXPIRY,
            json.dumps({
                "user_id": user.user_id,
                "username": user.username,
                "password": user.password,
                "created_at": user.created_at.isoformat()
            }))

    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def create_access_token_v2(data: dict):

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt, expire


async def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM])
        user_id = payload.get("user_id")
        username: str = payload.get("username")

        if username is None:
            raise InvalidCredentialsException()

        return TokenData(user_id=user_id, username=username)

    except JWTError:
        raise InvalidCredentialsException()


async def get_current_user(
        request: Request,
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_refresh_token_db)):

    token_data = await verify_access_token(token)
    user = await get_user(token_data.username, db, r)

    return user


async def get_current_user_optional(
        request: Request,
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_refresh_token_db)):

    try:
        token_data = await verify_access_token(token)
        user = await get_user(token_data.username, db, r)
    except InvalidCredentialsException:
        user = None

    return user


def create_refresh_token(
        data: dict,
        expires_delta: timedelta = None):

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt, expire


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, settings.REFRESH_SECRET_KEY,
                             algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("user_id")
    except JWTError:
        raise InvalidRefreshTokenException()
    return user_id
