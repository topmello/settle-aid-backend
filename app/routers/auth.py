from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

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
