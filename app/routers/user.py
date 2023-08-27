from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from passlib.context import CryptContext

from .. import schemas, models, oauth2

from ..database import get_db

from models.name_generator  import name_generator, generate_name


router = APIRouter(
    prefix='/user',
    tags=["User"]
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)

def verify(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)

@router.get('/generate', response_model=schemas.UsernameGen)
def generate_username(db: Session = Depends(get_db)):
    query = db.query(models.User.username)
    generated_name = generate_name(name_generator)
    # check if its unqiue
    while query.filter(models.User.username == generated_name).first():
        generated_name = generate_name(name_generator)
    return {"username": f"{generated_name.capitalize()}"}

@router.get('/{user_id}', response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(oauth2.get_current_user)):

    # Check if user_id is the same as current_user
    if user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    prompts = db.query(models.Prompt).filter(models.Prompt.created_by_user_id == user_id).all()
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user_out = schemas.UserOut(
        user_id=user.user_id,
        username=user.username,
        created_at=user.created_at,
        prompts=[schemas.Prompt.from_orm(prompt) for prompt in prompts]
    )

    return user_out


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