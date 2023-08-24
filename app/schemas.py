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

class SearchResult(BaseModel):
    name: str
    latitude: float
    longitude: float
    similarity: float
