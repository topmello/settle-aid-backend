from sqlalchemy.dialects.postgresql import insert
import json
import asyncio
from app import models
from app.database import get_db
from app.redis import get_redis_feed_db_context
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


async def generate_route_image():
    """Generate route image"""
    db = next(get_db())

    routes_with_prompts = (
        db.query(
            models.Route,
            models.Prompt.prompt,
            models.Prompt.location_type
        )
        .join(
            models.Prompt_Route,
            models.Route.route_id == models.Prompt_Route.route_id
        )
        .join(
            models.Prompt,
            models.Prompt.prompt_id == models.Prompt_Route.prompt_id)
        .all()
    )
    for route, prompt, location_type in routes_with_prompts:
        location_type_ = location_type[0] if location_type else None
        prompt_ = prompt[0] if prompt else None

        async with get_redis_feed_db_context() as r:
            route_image_name = await r.get(
                f"route_image_name:{location_type_}:{prompt_}"
            )
            if route_image_name != "null" and route_image_name is not None:

                route_image_name = get_similar_image(
                    prompt_,
                    location_type_
                )
                print(route_image_name)

                await r.set(
                    f"route_image_name:{location_type}:{prompt_}",
                    route_image_name
                )

        route_image = models.Route_Image(
            route_id=route.route_id, route_image_name=route_image_name
        )

        if db.query(models.Route_Image).filter(
            models.Route_Image.route_id == route.route_id
        ).first():
            print("Route image already exists")
            continue

        db.add(route_image)
        db.commit()


def main():
    for data_type in DATA_FILES_MODELS.keys():
        insert_into_table(data_type)

    asyncio.run(generate_route_image())


if __name__ == "__main__":
    main()
