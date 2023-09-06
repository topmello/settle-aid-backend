from pydantic import BaseModel, ValidationError, field_validator, constr
from datetime import datetime


class UserCreate(BaseModel):
    username: constr(max_length=20, min_length=4,
                     pattern="^[a-zA-Z][a-zA-Z0-9_]{3,19}$",
                     to_lower=True)
    password: constr(max_length=20, min_length=4,
                     pattern="^[a-zA-Z0-9!@#$%^&*]{4,20}$")


class LoginRequest(BaseModel):
    username: constr(max_length=20, min_length=4,
                     pattern="^[a-zA-Z][a-zA-Z0-9_]{3,19}$",
                     to_lower=True)
    password: constr(max_length=20, min_length=4,
                     pattern="^[a-zA-Z0-9!@#$%^&*]{4,20}$")


class User(BaseModel):
    user_id: int
    username: str
    password: str
    created_at: datetime


class Prompt(BaseModel):
    prompt_id: int
    created_by_user_id: int
    prompt: list[constr(max_length=50)]
    location_type: list[str]
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

    @field_validator('location_type')
    def check_location_type(cls, v):
        allowed_location_types = ['landmark',
                                  'restaurant', 'grocery', 'pharmacy']
        if v not in allowed_location_types:
            raise ValueError(
                f'location_type must be one of {allowed_location_types}')
        return v


class QuerySeq(BaseModel):
    query: list[constr(max_length=50)]
    location_type: list[str]
    longitude: float
    latitude: float
    distance_threshold: float
    similarity_threshold: float

    @field_validator('location_type')
    def check_location_type(cls, v):

        allowed_location_types = ['landmark',
                                  'restaurant', 'grocery', 'pharmacy']
        if not all(location_type in allowed_location_types for location_type in v):
            raise ValueError(
                f'location_type must be one of {allowed_location_types}')
        return v


class RouteQuery(QuerySeq):
    route_type: str = "walking"

    @field_validator('route_type')
    def check_route_type(cls, v):
        allowed_route_types = ['driving', 'walking', 'cycling']
        if v not in allowed_route_types:
            raise ValueError(
                f'route_type must be one of {allowed_route_types}')
        return v


class SearchResult(BaseModel):
    name: str
    latitude: float
    longitude: float
    similarity: float


class RouteOut(BaseModel):
    locations: list[str]
    locations_coordinates: list[dict[str, float]]
    route: list[dict[str, float]]
    instructions: list[str]
    duration: float


class UsernameGen(BaseModel):
    username: str


class TranslateQuery(BaseModel):
    texts: list[constr(max_length=50)]


class TranslateRes(BaseModel):
    results: list[str]
