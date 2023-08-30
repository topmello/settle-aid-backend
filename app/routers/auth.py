from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

from ..database import get_db

from .. import models, schemas, oauth2
from .user import verify

router = APIRouter(
    tags=["Authentication"]
)

@router.post('/login', response_model=schemas.Token)
def login(user_credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    # user_credentials contains username and password
    
    user_query = db.query(models.User).filter(models.User.username == user_credentials.username)


    if user_query.first() == None:
        raise HTTPException(status_code=403, detail="Invalid credentials")
        
    if not verify(user_credentials.password, user_query.first().password):
        raise HTTPException(status_code=403, detail="Invalid credentials")

    # Generate JWT token
    access_token = oauth2.create_access_token(data={
        "user_id": user_query.first().user_id,
        "username": user_credentials.username
        })
    
    return {"access_token": access_token, "token_type": "bearer"}