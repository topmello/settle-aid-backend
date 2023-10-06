from sqlalchemy.dialects.postgresql import insert
import json

from app.database import get_db
from app import models

from app.huggingface_models import get_similar_image

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


def generate_route_image():
    """Generate route image"""
    db = next(get_db())
    routes = db.query(models.Route).all()

    for route in routes:
        route_image_name = get_similar_image(route.locations[0])
        route_image = models.Route_Image(
            route_id=route.route_id, route_image_name=route_image_name
        )

        if db.query(models.Route_Image).filter(
            models.Route_Image.route_id == route.route_id
        ).first():
            continue
        db.add(route_image)
        db.commit()


def main():
    for data_type in DATA_FILES_MODELS.keys():
        insert_into_table(data_type)

    generate_route_image()


if __name__ == "__main__":
    main()
