from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.context import CryptContext
from typing import List, Dict

from .. import schemas, models, oauth2

from ..database import get_db
from ..limiter import limiter
from ..exceptions import UserNotFoundException, UserAlreadyExistsException, NotAuthorisedException

from models.name_generator import name_generator, generate_name


router = APIRouter(
    prefix='/user',
    tags=["User"]
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)


def verify(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


@router.get('/generate/', response_model=schemas.UsernameGen)
@limiter.limit("1/second")
async def generate_username(
        request: Request,
        db: Session = Depends(get_db)):
    """
    Generate a unique username.

    Args:
    - None: This function does not take in any arguments.

    Raises:
    - None: This function does not explicitly raise any exceptions, but internal methods or dependencies might raise exceptions if any issues occur.

    Returns:
    - dict: A dictionary containing the generated username.

    Note:
    - The generated username using Transformer decoding architecture and is checked for uniqueness against the database.
    """

    query = db.query(models.User.username)
    generated_name = generate_name(name_generator)
    # check if its unqiue
    while query.filter(models.User.username == generated_name).first():
        generated_name = generate_name(name_generator)
    return {"username": f"{generated_name.capitalize()}"}


@router.get('/{user_id}/', response_model=schemas.UserOut)
@limiter.limit("1/second")
async def get_user(
        request: Request,
        user_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(oauth2.get_current_user)):
    """
    Retrieve a user by its ID, along with their latest prompts.

    Args:
    - user_id (int): The ID of the user to be fetched.
    - Logged in required: The user must be logged in to retrieve their own details.

    Raises:
    - NotAuthorisedException: If the user_id does not match the current authenticated user.
    - UserNotFoundException: If the user does not exist in the database.

    Returns:
    - schemas.UserOut: User details along with their latest ten prompts.


    """

    # Check if user_id is the same as current_user
    if user_id != current_user.user_id:
        raise NotAuthorisedException()

    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    prompts = db.query(models.Prompt).filter(
        models.Prompt.created_by_user_id == user_id).limit(10).all()

    if user is None:
        raise UserNotFoundException()

    user_out = schemas.UserOut(
        user_id=user.user_id,
        username=user.username,
        created_at=user.created_at,
        prompts=[schemas.Prompt.from_orm(prompt) for prompt in prompts]
    )

    return user_out


@router.post('/', status_code=201, response_model=schemas.User)
@limiter.limit("5/minute")
async def create_user(
        request: Request,
        user: schemas.UserCreate,
        db: Session = Depends(get_db)):

    """
    Create a new user in the database.

    Args:
    - user (schemas.UserCreate): The user details to be created.

    Raises:
    - UserAlreadyExistsException: If the username already exists in the database.

    Returns:
    - models.User: The created user model.
    """

    if db.query(models.User).filter(models.User.username == user.username).first():
        raise UserAlreadyExistsException()

    # Hash password
    hashed_password = hash(user.password)
    user.password = hashed_password

    new_user = models.User(**user.model_dump())

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
