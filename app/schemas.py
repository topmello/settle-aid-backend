from pydantic import BaseModel, ValidationError, field_validator, root_validator, constr, conint
from datetime import datetime
from .models import Route
from typing import Optional


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


class PromptV2(BaseModel):
    prompt_id: int
    created_by_user_id: int
    prompt: list[constr(max_length=50)]
    negative_prompt: list[constr(max_length=50)]
    location_type: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RouteOut(BaseModel):
    locations: list[str]
    locations_coordinates: list[dict[str, float]]
    route: list[dict[str, float]]
    instructions: list[str]
    duration: float


class RouteOutV2(BaseModel):
    route_id: int
    locations: list[str]
    locations_coordinates: list[dict[str, float]]
    route: list[dict[str, float]]
    instructions: list[str]
    duration: float
    created_at: datetime

    @classmethod
    def from_orm(cls, route: Route) -> "RouteOutV2":
        # Convert latitudes and longitudes to list of dictionaries
        locations_coordinates = [
            {"latitude": lat, "longitude": lon}
            for lat, lon in zip(route.location_latitudes, route.location_longitudes)
        ]

        route_coordinates = [
            {"latitude": lat, "longitude": lon}
            for lat, lon in zip(route.route_latitudes, route.route_longitudes)
        ]

        return cls(
            route_id=route.route_id,
            locations=route.locations,
            locations_coordinates=locations_coordinates,
            route=route_coordinates,
            instructions=route.instructions,
            duration=route.duration,
            created_at=route.created_at,
        )


class RouteVoteOut(BaseModel):
    route: RouteOutV2
    num_votes: int


class RouteVoteOutUser(BaseModel):
    route: RouteOutV2
    num_votes: int
    voted_by_user: bool


class UserOut(BaseModel):
    user_id: int
    username: str
    created_at: datetime
    prompts: list[Prompt]


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenV2(BaseModel):
    user_id: int
    username: str
    access_token: str
    token_type: str
    access_token_expire: datetime
    refresh_token: str
    refresh_token_expire: datetime


class RefreshTokenIn(BaseModel):
    refresh_token: str


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
                                  'restaurant',
                                  'grocery',
                                  'pharmacy']
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


class RouteQueryV2(QuerySeq):
    negative_query: list[constr(max_length=50)]
    negative_similarity_threshold: float
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


class UsernameGen(BaseModel):
    username: str


class TranslateQuery(BaseModel):
    texts: list[constr(max_length=50)]


class TranslateRes(BaseModel):
    results: list[str]


class VoteIn(BaseModel):
    route_id: int
    vote: bool


class TrackRoomOut(BaseModel):
    room_id: str


class Challenge(BaseModel):
    name: str
    type: str


class UserChallengeOut(BaseModel):
    challenge: Challenge
    year: int
    month: int
    day: int
    progress: float


class DistanceTravelledChallenge(BaseModel):
    steps: conint(ge=0, le=50000)


class RouteGenerationChallenge(BaseModel):
    routes_generated: int


class RouteFavChallenge(BaseModel):
    routes_favourited_shared: int


class ChallengeScoreOut(BaseModel):
    date: datetime
    score: float
    distance_travelled_score: Optional[float]
    route_generation_score: Optional[float]
    favourite_sharing_score: Optional[float]


class LeaderboardOut(BaseModel):
    username: str
    score: float
