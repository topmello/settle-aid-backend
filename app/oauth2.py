from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .config import settings
from .schemas import TokenData
from .database import get_db
from . import models
import aioredis
from .redis import get_redis_logs_db, log_to_redis

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


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


async def verify_access_token(
        token: str,
        credentials_exception,
        r_logger: aioredis.Redis = Depends(get_redis_logs_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM])
        user_id = payload.get("user_id")
        username: str = payload.get("username")

        if username is None:
            raise credentials_exception

        return TokenData(user_id=user_id, username=username)

    except JWTError:
        raise credentials_exception


async def get_current_user(
        request: Request,
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
        r_logger: aioredis.Redis = Depends(get_redis_logs_db)):

    endpoint = request.url.path

    await log_to_redis("Auth", f"Endpoint {endpoint} - Retrieving current user", r_logger)

    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = await verify_access_token(token, credentials_exception)
    user_query = db.query(models.User).filter(
        models.User.user_id == token_data.user_id)

    await log_to_redis("Auth", f"Endpoint {endpoint} - Current user retrieved", r_logger)

    return user_query.first()


def create_refresh_token(
        data: dict,
        expires_delta: timedelta = None,
        r_logger: aioredis.Redis = Depends(get_redis_logs_db)):

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, settings.REFRESH_SECRET_KEY,
                             algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("user_id")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return user_id
