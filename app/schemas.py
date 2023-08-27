from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    user_id: int
    username: str
    password: str
    created_at: datetime

class Prompt(BaseModel):
    prompt_id: int
    created_by_user_id: int
    prompt: str
    location_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    user_id: int
    username: str
    created_at: datetime
    prompts: list[Prompt]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: int
    username: str

class Query(BaseModel):
    query: str
    location_type: str
    longitude: float
    latitude: float
    distance_threshold: float
    similarity_threshold: float

class QuerySeq(BaseModel):
    query: list[str]
    location_type: list[str]
    longitude: float
    latitude: float
    distance_threshold: float
    similarity_threshold: float

class SearchResult(BaseModel):
    name: str
    latitude: float
    longitude: float
    similarity: float

class UsernameGen(BaseModel):
    username: str