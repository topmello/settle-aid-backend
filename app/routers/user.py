from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from .. import schemas, models

from ..database import get_db

from ..name_generator import name_generator, generate_name



router = APIRouter(
    prefix='/user',
    tags=["user"]
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)

def verify(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)

@router.get('/', response_model=schemas.UsernameGen)
def generate_username(db: Session = Depends(get_db)):
    query = db.query(models.User.username)
    generated_name = generate_name(name_generator)
    # check if its unqiue
    while query.filter(models.User.username == generated_name).first():
        generated_name = generate_name(name_generator)
    return {"username": f"{generated_name.capitalize()}"}

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