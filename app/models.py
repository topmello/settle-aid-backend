from .database import Base

from sqlalchemy import Column, Integer, String, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import mapped_column
from pgvector.sqlalchemy import Vector

from geoalchemy2 import Geometry

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),server_default = text("now()"), nullable=False)

class Prompt(Base):
    __tablename__ = "prompts"

    prompt_id = Column(Integer, primary_key=True, index=True)
    prompt_embeding = mapped_column(Vector(384))

class Landmark(Base):
    __tablename__ = "landmarks"

    landmark_id = Column(Integer, primary_key=True, index=True)
    landmark_coord = Column(Geometry('POINT'))
