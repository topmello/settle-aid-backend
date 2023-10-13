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


def update_challenge_table():
    file, Model = DATA_FILES_MODELS.get("challenge", (None, None))

    with open(file, 'r') as f:
        data = json.load(f)

    db = next(get_db())

    challenges = db.query(Model).all()

    for challenge, data in zip(challenges, data):
        challenge.type = data['type']

    db.commit()


def main():

    update_challenge_table()


if __name__ == "__main__":
    main()
