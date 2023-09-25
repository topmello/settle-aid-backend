from .database import Base

from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, text, ForeignKey, Boolean, ARRAY, Index, UniqueConstraint
from sqlalchemy.orm import mapped_column
from pgvector.sqlalchemy import Vector

from geoalchemy2 import Geometry


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    user_id = Column(Integer, ForeignKey('users.user_id'),
                     nullable=False, primary_key=True)
    token = Column(String, nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)


class Prompt(Base):
    __tablename__ = "prompts"

    prompt_id = Column(Integer, primary_key=True, index=True)
    created_by_user_id = Column(
        Integer, ForeignKey("users.user_id"), nullable=False)
    prompt = Column(ARRAY(String), nullable=False)
    negative_prompt = Column(ARRAY(String), nullable=True)
    location_type = Column(ARRAY(String), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)


class Route(Base):
    __tablename__ = "routes"

    route_id = Column(Integer, primary_key=True, index=True)
    created_by_user_id = Column(
        Integer, ForeignKey("users.user_id"), nullable=False)
    locations = Column(ARRAY(String), nullable=False)
    location_latitudes = Column(ARRAY(Float), nullable=False)
    location_longitudes = Column(ARRAY(Float), nullable=False)
    route_latitudes = Column(ARRAY(Float), nullable=False)
    route_longitudes = Column(ARRAY(Float), nullable=False)
    instructions = Column(ARRAY(String), nullable=False)
    duration = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)


class User_Route_Vote(Base):
    __tablename__ = "user_route_votes"

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"),
                     nullable=False, primary_key=True)
    route_id = Column(Integer, ForeignKey("routes.route_id", ondelete="CASCADE"),
                      nullable=False, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)


class Prompt_Route(Base):
    __tablename__ = "prompt_routes"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey(
        "prompts.prompt_id"), nullable=False)
    created_by_user_id = Column(
        Integer, ForeignKey("users.user_id"), nullable=False)
    route_id = Column(Integer, ForeignKey("routes.route_id"), nullable=False)


class Landmark(Base):
    __tablename__ = "landmarks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    coord = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    embedding = mapped_column(Vector(384))


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    coord = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    embedding = mapped_column(Vector(384))


class Grocery(Base):
    __tablename__ = "groceries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    coord = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    embedding = mapped_column(Vector(384))


class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    coord = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    embedding = mapped_column(Vector(384))


class Prompt_Landmark(Base):
    __tablename__ = "prompt_landmarks"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey(
        "prompts.prompt_id"), nullable=False)
    created_by_user_id = Column(
        Integer, ForeignKey("users.user_id"), nullable=False)
    location_id = Column(Integer, ForeignKey("landmarks.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)


class Prompt_Restaurant(Base):
    __tablename__ = "prompt_restaurants"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey(
        "prompts.prompt_id"), nullable=False)
    created_by_user_id = Column(
        Integer, ForeignKey("users.user_id"), nullable=False)
    location_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)


class Prompt_Grocery(Base):
    __tablename__ = "prompt_groceries"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey(
        "prompts.prompt_id"), nullable=False)
    created_by_user_id = Column(
        Integer, ForeignKey("users.user_id"), nullable=False)
    location_id = Column(Integer, ForeignKey("groceries.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)


class Prompt_Pharmacy(Base):
    __tablename__ = "prompt_pharmacies"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey(
        "prompts.prompt_id"), nullable=False)
    created_by_user_id = Column(
        Integer, ForeignKey("users.user_id"), nullable=False)
    location_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    grade = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)


class User_Challenge(Base):
    __tablename__ = "user_challenges"

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"),
                     nullable=False, primary_key=True)
    challenge_id = Column(Integer, ForeignKey("challenges.challenge_id", ondelete="CASCADE"),
                          nullable=False, primary_key=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    idx_year_month_day = Index('idx_year_month_day', year, month, day)
    progress = Column(Float, nullable=False, default=0.0)

    __table_args__ = (UniqueConstraint('user_id', 'challenge_id',
                      'year', 'month', 'day', name='uix_user_challenge_date'),)
