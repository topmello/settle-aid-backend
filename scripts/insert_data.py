from sqlalchemy.dialects.postgresql import insert
import json
from app import models
from app.database import get_db

# Dictionary mapping location types to models
DATA_FILES_MODELS = {
    "landmark": ("data/landmarks.json", models.Landmark),
    "restaurant": ("data/restaurants_2019.json", models.Restaurant),
    "grocery": ("data/supermarkets.json", models.Grocery),
    "pharmacy": ("data/pharmacies.json", models.Pharmacy),
    "challenge": ("data/challenges.json", models.Challenge)
}


def insert_into_table(data_type: str):
    """Insert data into database"""
    file, Model = DATA_FILES_MODELS.get(data_type, (None, None))

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
    for data_type in DATA_FILES_MODELS.keys():
        insert_into_table(data_type)


if __name__ == "__main__":
    main()
