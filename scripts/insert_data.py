from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import json

from app.database import get_db
from app import models

# Dictionary mapping location types to models
LOCATION_TYPE_MODELS = {
    "landmark": models.Landmark,
    "restaurant": models.Restaurant,
    "grocery": models.Grocery,
    "pharmacy": models.Pharmacy,
}

LOCATION_TYPE_DATA = {
    "landmark": "data/landmarks.json",
    "restaurant": "data/restaurants_2019.json",
    "grocery": "data/supermarkets.json",
    "pharmacy": "data/pharmacies.json",
}


def insert_into_table(location_type: str):
    """Insert data into database"""
    file = LOCATION_TYPE_DATA.get(location_type)
    Model = LOCATION_TYPE_MODELS.get(location_type)
    if not file or not Model:
        raise ValueError("Location type not found")

    with open(file, 'r') as f:
        data = json.load(f)

    db = next(get_db())
    stmt = insert(Model).values(
        data).on_conflict_do_nothing(index_elements=['id'])
    db.execute(stmt)
    db.commit()


def main():
    for location_type in LOCATION_TYPE_MODELS.keys():
        insert_into_table(location_type)


if __name__ == "__main__":
    main()
