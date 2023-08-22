from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from .. import schemas, models

from ..database import get_db

router = APIRouter(
    prefix='/user',
    tags=["user"]
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

def verify(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)

@router.post('/', status_code=201, response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    print('Creaing user')
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_password = hash(user.password)
    user.password = hashed_password

    new_user = models.User(**user.dict())
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user