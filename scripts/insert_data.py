from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import json

from app.database import get_db
from app import models


def insert_landmarks():
    """Insert landmarks into database"""
    with open('data/landmarks.json', 'r') as f:
            landmarks = json.load(f)

    db = next(get_db())
    stmt = insert(models.Landmark).values(landmarks).on_conflict_do_nothing(index_elements=['landmark_id'])
    db.execute(stmt)
    db.commit()

def insert_restaurants():
    """Insert restaurants into database"""
    with open('data/restaurants_2019.json', 'r') as f:
            restaurants = json.load(f)

    db = next(get_db())
    stmt = insert(models.Restaurant).values(restaurants).on_conflict_do_nothing(index_elements=['restaurant_id'])
    db.execute(stmt)
    db.commit()
    
if __name__ == "__main__":
    insert_landmarks()