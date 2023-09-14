from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from jose import jwt
import json
import aioredis

from ..database import get_db
from ..redis import get_redis_refresh_token_db, get_redis_logs_db, log_to_redis
from ..config import settings
from ..limiter import limiter

from .. import models, schemas, oauth2
from .user import verify

router = APIRouter(
    prefix="/login",
    tags=["Authentication"]
)


@router.post('/', response_model=schemas.Token)
@limiter.limit("5/second")
async def login(
        request: Request,
        user_credentials: schemas.LoginRequest,
        db: Session = Depends(get_db),
        r_logger: aioredis.Redis = Depends(get_redis_logs_db)):
    await log_to_redis("Auth", f"{request.method} request to {request.url.path}", r_logger)
    # user_credentials contains username and password
    user_query = db.query(models.User).filter(
        models.User.username == user_credentials.username)

    if user_query.first() == None or not verify(user_credentials.password, user_query.first().password):

        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate JWT token
    access_token = oauth2.create_access_token(data={
        "user_id": user_query.first().user_id,
        "username": user_credentials.username
    })

    return {"access_token": access_token, "token_type": "bearer"}


@router.post('/v2/', response_model=schemas.TokenV2)
@limiter.limit("5/second")
async def login(
        request: Request,
        user_credentials: schemas.LoginRequest,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_refresh_token_db),
        r_logger: aioredis.Redis = Depends(get_redis_logs_db)):
    await log_to_redis("Auth", f"{request.method} request to {request.url.path}", r_logger)
    # user_credentials contains username and password
    user_query = db.query(models.User).filter(
        models.User.username == user_credentials.username)

    if user_query.first() == None or not verify(user_credentials.password, user_query.first().password):

        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = user_query.first().user_id
    # Delete existing refresh token from Redis
    await r.delete(f"refresh_token:{user_id}")

    # Generate JWT token
    access_token, access_token_expire = oauth2.create_access_token_v2(data={
        "user_id": user_id,
        "username": user_credentials.username
    })
    # Generate refresh token
    refresh_token_data = {"user_id": user_id}
    refresh_token = oauth2.create_refresh_token(data=refresh_token_data)
    refresh_token_expiry = datetime.utcnow(
    ) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Store refresh token and its expiry in Redis as a JSON string
    token_data = {
        "token": refresh_token,
        "expires_at": refresh_token_expiry.isoformat()
    }
    ttl = (refresh_token_expiry - datetime.utcnow()).total_seconds()
    await r.setex(f"refresh_token:{user_query.first().user_id}", int(
        ttl), json.dumps(token_data))

    await log_to_redis("Auth", f"User {user_id} logged in", r_logger)
    return {
        "user_id": user_id,
        "access_token": access_token,
        "token_type": "bearer",
        "access_token_expire": access_token_expire,
        "refresh_token": refresh_token,
        "refresh_token_expire": refresh_token_expiry
    }


@router.post('/v2/refresh/', response_model=schemas.TokenV2)
@limiter.limit("5/second")
async def refresh_token(
        request: Request,
        refresh_token: schemas.RefreshTokenIn,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_refresh_token_db),
        r_logger: aioredis.Redis = Depends(get_redis_logs_db)):
    await log_to_redis("Auth", f"{request.method} request to {request.url.path}", r_logger)
    # Verify the JWT signature and get the user_id
    user_id = oauth2.verify_refresh_token(refresh_token.refresh_token)

    # Retrieve the stored token data from Redis
    stored_token_data = await r.get(f"refresh_token:{user_id}")
    if not stored_token_data:
        await log_to_redis("Auth", f"Refresh token not existed", r_logger)
        raise HTTPException(
            status_code=401, detail="Refresh token not existed")

    # Parse the JSON string to get the token and its expiration time
    token_data = json.loads(stored_token_data)
    if token_data["token"] != refresh_token.refresh_token:
        await log_to_redis("Auth", f"Invalid refresh token", r_logger)
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Check if the token has expired
    if datetime.fromisoformat(token_data["expires_at"]) < datetime.utcnow():
        await log_to_redis("Auth", f"Refresh token has expired", r_logger)
        raise HTTPException(
            status_code=401, detail="Refresh token has expired")

    # Generate a new access token
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    access_token, access_token_expire = oauth2.create_access_token_v2(
        data={"user_id": user.user_id, "username": user.username})

    return {
        "user_id": user_id,
        "access_token": access_token,
        "token_type": "bearer",
        "access_token_expire": access_token_expire,
        "refresh_token": token_data["token"],
        "refresh_token_expire": token_data["expires_at"]
    }
