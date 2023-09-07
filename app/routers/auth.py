from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from jose import jwt

from ..limiter import rate_limited_route
from ..database import get_db

from .. import models, schemas, oauth2
from .user import verify

router = APIRouter(
    tags=["Authentication"]
)

ip_blocklist = {}
ip_attempts = {}
BLOCK_DURATION = timedelta(minutes=1)
MAX_ATTEMPTS = 5


def check_blocked_ip(request: Request):
    ip = request.client.host
    if ip in ip_blocklist:
        block_time = ip_blocklist[ip]
        if datetime.now() - block_time <= BLOCK_DURATION:
            raise HTTPException(
                status_code=403, detail="Too many failed attempts. Please try again later.")
        else:
            # Unblock the IP after the duration
            del ip_blocklist[ip]
            del ip_attempts[ip]
    return True


@router.post('/login', response_model=schemas.Token)
def login(
        user_credentials: schemas.LoginRequest,
        request: Request,
        db: Session = Depends(get_db),
        _rate_limited: bool = Depends(rate_limited_route),
        _ip_check: bool = Depends(check_blocked_ip)):

    ip = request.client.host

    # user_credentials contains username and password
    user_query = db.query(models.User).filter(
        models.User.username == user_credentials.username)

    if user_query.first() == None or not verify(user_credentials.password, user_query.first().password):
        if ip in ip_attempts:
            ip_attempts[ip] += 1
        else:
            ip_attempts[ip] = 1

        if ip_attempts[ip] >= MAX_ATTEMPTS:
            ip_blocklist[ip] = datetime.now()

        raise HTTPException(status_code=403, detail="Invalid credentials")

    # If successful login, reset the attempt count for the IP
    ip_attempts.pop(ip, None)

    # Generate JWT token
    access_token = oauth2.create_access_token(data={
        "user_id": user_query.first().user_id,
        "username": user_credentials.username
    })

    return {"access_token": access_token, "token_type": "bearer"}


@router.post('/v2/login', response_model=schemas.TokenV2)
def login(
        user_credentials: schemas.LoginRequest,
        request: Request,
        db: Session = Depends(get_db),
        _rate_limited: bool = Depends(rate_limited_route),
        _ip_check: bool = Depends(check_blocked_ip)):

    ip = request.client.host

    # user_credentials contains username and password
    user_query = db.query(models.User).filter(
        models.User.username == user_credentials.username)

    if user_query.first() == None or not verify(user_credentials.password, user_query.first().password):
        if ip in ip_attempts:
            ip_attempts[ip] += 1
        else:
            ip_attempts[ip] = 1

        if ip_attempts[ip] >= MAX_ATTEMPTS:
            ip_blocklist[ip] = datetime.now()

        raise HTTPException(status_code=403, detail="Invalid credentials")

    # If successful login, reset the attempt count for the IP
    ip_attempts.pop(ip, None)

    # Check if a refresh token already exists for the user
    existing_refresh_token = db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == user_query.first().user_id).first()

    # If a refresh token exists, delete it
    if existing_refresh_token:
        db.delete(existing_refresh_token)
        db.commit()

    # Generate JWT token
    access_token = oauth2.create_access_token(data={
        "user_id": user_query.first().user_id,
        "username": user_credentials.username
    })
    # Generate refresh token
    refresh_token_data = {"user_id": user_query.first().user_id}
    refresh_token = oauth2.create_refresh_token(data=refresh_token_data)
    refresh_token_expiry = datetime.utcnow() + timedelta(days=7)

    # Store refresh token in database
    db_refresh_token = models.RefreshToken(user_id=user_query.first(
    ).user_id, token=refresh_token, expires_at=refresh_token_expiry)
    db.add(db_refresh_token)
    db.commit()

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}


@router.post('/v2/token/refresh', response_model=schemas.TokenV2)
def refresh_token(refresh_token: schemas.RefreshTokenIn, db: Session = Depends(get_db)):
    user_id = oauth2.verify_refresh_token(refresh_token.refresh_token, db)

    # Generate a new access token
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    access_token = oauth2.create_access_token(
        data={"user_id": user.user_id, "username": user.username})

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token.refresh_token}
