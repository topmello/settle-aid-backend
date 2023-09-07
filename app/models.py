from .database import Base

from sqlalchemy import Column, Integer, String, TIMESTAMP, text, ForeignKey, Boolean, ARRAY
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

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    token = Column(String, nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)


class Prompt(Base):
    __tablename__ = "prompts"

    prompt_id = Column(Integer, primary_key=True, index=True)
    created_by_user_id = Column(
        Integer, ForeignKey("users.user_id"), nullable=False)
    prompt = Column(ARRAY(String), nullable=False)
    location_type = Column(ARRAY(String), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)


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


class Prompt_Landmark_Vote(Base):
    __tablename__ = "prompt_landmark_votes"

    id = Column(Integer, primary_key=True)
    prompt_location_id = Column(Integer, ForeignKey(
        "prompt_landmarks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    # True for upvote, False for downvote
    vote = Column(Boolean, nullable=False)
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


class Prompt_Restaurant_Vote(Base):
    __tablename__ = "prompt_restaurant_votes"

    id = Column(Integer, primary_key=True)
    prompt_location_id = Column(Integer, ForeignKey(
        "prompt_restaurants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    # True for upvote, False for downvote
    vote = Column(Boolean, nullable=False)
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


class Prompt_Grocery_Vote(Base):
    __tablename__ = "prompt_grocery_votes"

    id = Column(Integer, primary_key=True)
    prompt_location_id = Column(Integer, ForeignKey(
        "prompt_groceries.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    # True for upvote, False for downvote
    vote = Column(Boolean, nullable=False)
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


class Prompt_Pharmacy_Vote(Base):
    __tablename__ = "prompt_pharmacy_votes"

    id = Column(Integer, primary_key=True)
    prompt_location_id = Column(Integer, ForeignKey(
        "prompt_pharmacies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    # True for upvote, False for downvote
    vote = Column(Boolean, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)
