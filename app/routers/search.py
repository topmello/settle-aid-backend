from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from sqlalchemy import select, desc, func, text
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement


import numpy as np

from sentence_transformers import SentenceTransformer

from ..database import get_db


from ..mapbox import get_route

from ..limiter import limiter
from ..exceptions import LocationNotFoundException, InvalidSearchQueryException
from .. import models, schemas, oauth2


router = APIRouter(
    prefix="/search",
    tags=["Search"],
    responses={404: {"description": "Not found"}},
)

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Dictionary mapping location types to models
LOCATION_TYPE_MODELS = {
    "landmark": models.Landmark,
    "restaurant": models.Restaurant,
    "grocery": models.Grocery,
    "pharmacy": models.Pharmacy
}

PROMPT_LOCATION_TYPE_MODELS = {
    "landmark": models.Prompt_Landmark,
    "restaurant": models.Prompt_Restaurant,
    "grocery": models.Prompt_Grocery,
    "pharmacy": models.Prompt_Pharmacy
}


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)


@router.post("/route/", response_model=schemas.RouteOut)
@limiter.limit("1/second")
async def search_by_query_seq(
        request: Request,
        querys: schemas.RouteQuery,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)):
    """
    Search for a route based on user queries and the current location.

    Args:
    - querys (schemas.RouteQuery): The user query data containing location type, latitude, longitude, distance threshold, similarity threshold, and route type.
    - Logged in required: The user must be logged in to search for a route.

    Raises:
    - LocationNotFoundException: If no matching location is found for a given query.

    Returns:
    - schemas.RouteOut: The resulting route including locations, route coordinates, instructions, and duration.
    """

    results = []
    seen_places = set()

    prompt = models.Prompt(
        created_by_user_id=current_user.user_id,
        prompt=querys.query,
        location_type=querys.location_type
    )

    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    current_location = WKTElement(
        f'POINT({querys.longitude} {querys.latitude})', srid=4326)

    for i, query in enumerate(querys.query):
        query_embeding = model.encode([query])[0]

        # Dynamically get the correct model based on location type
        Model = LOCATION_TYPE_MODELS.get(querys.location_type[i])

        if not Model:
            raise LocationNotFoundException()

        query_result = (
            db.query(
                Model.id.label('id'),
                Model.name.label('name'),
                func.st_y(Model.coord).label('latitude'),
                func.st_x(Model.coord).label('longitude'),
                (1-Model.embedding.cosine_distance(query_embeding)).label('similarity')
            )
            .filter(func.ST_Distance(
                func.ST_Transform(Model.coord, 3857),
                func.ST_Transform(current_location, 3857)
            ) < querys.distance_threshold)
            .filter((1-Model.embedding.cosine_distance(query_embeding)) > querys.similarity_threshold)
            # Exclude places already seen
            .filter(Model.name.notin_(seen_places))
            .order_by(desc('similarity'))
            .limit(10)


        )

        locations = query_result.all()

        if locations:
            similarities = [result.similarity for result in locations]
            probs = softmax(similarities)

            chosen_idx = np.random.choice(len(locations), p=probs)
            chosen_location = locations[chosen_idx]

            results.append(chosen_location)
            current_location = WKTElement(
                f'POINT({chosen_location.longitude} {chosen_location.latitude})', srid=4326)
            seen_places.add(chosen_location.name)

        else:
            raise LocationNotFoundException()

        prompt_location = PROMPT_LOCATION_TYPE_MODELS.get(
            querys.location_type[i])
        insert_prompt_location = prompt_location(
            prompt_id=prompt.prompt_id,
            created_by_user_id=current_user.user_id,
            location_id=chosen_location.id
        )

        db.add(insert_prompt_location)
        db.commit()

    if results == []:
        raise LocationNotFoundException()

    # Create route
    location_names = [location.name for location in results]
    coordinates = [{"latitude": querys.latitude,
                    "longitude": querys.longitude}]
    for location in results:
        coordinates.append({"latitude": location.latitude,
                           "longitude": location.longitude})

    coordinates_str = [
        f"{c['longitude']}, {c['latitude']}" for c in coordinates]

    route = get_route(';'.join(coordinates_str), profile=querys.route_type)
    route_coordinates = route['routes'][0]['geometry']['coordinates']
    route_coordinates = [{"latitude": coord[1], "longitude": coord[0]}
                         for coord in route_coordinates]

    instructions = []
    for leg in route['routes'][0]['legs']:
        for step in leg['steps']:
            instructions.append(step['maneuver']['instruction'])

    duration = route['routes'][0]['duration']

    out = schemas.RouteOut(
        locations=location_names,
        locations_coordinates=coordinates,
        route=route_coordinates,
        instructions=instructions,
        duration=duration
    )
    return out


@router.post("/v2/route/", response_model=schemas.RouteOutV2)
@limiter.limit("1/second")
async def search_by_query_seq_v2(
        request: Request,
        querys: schemas.RouteQueryV2,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)):
    """
    Search for a route based on user queries, negative queries, and the current location (Version 2).

    This endpoint allows users to provide negative queries to exclude certain results.

    Args:
    - querys (schemas.RouteQueryV2): The user query data including location type, latitude, longitude, distance threshold, similarity threshold, negative query, negative similarity threshold, and route type.
    - Logged in required: The user must be logged in to search for a route.

    Raises:
    - LocationNotFoundException: If no matching location is found for a given query.
    - InvalidSearchQueryException: If the provided queries are inconsistent in length or type.

    Returns:
    - schemas.RouteOutV2: The resulting route including route ID, locations, route coordinates, instructions, and duration.
    """

    if querys.negative_query is None:
        querys.negative_query = ["" for _ in range(len(querys.query))]
        querys.negative_similarity_threshold = 0
    if len(querys.location_type) != len(querys.query):
        raise InvalidSearchQueryException()
    if len(querys.location_type) != len(querys.negative_query):
        raise InvalidSearchQueryException()

    results = []
    seen_places = set()

    prompt = models.Prompt(
        created_by_user_id=current_user.user_id,
        prompt=querys.query,
        negative_prompt=querys.negative_query,
        location_type=querys.location_type
    )

    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    current_location = WKTElement(
        f'POINT({querys.longitude} {querys.latitude})', srid=4326)

    for i, query in enumerate(querys.query):
        query_embeding = model.encode([query])[0]
        negative_query_embeding = model.encode([querys.negative_query[i]])[0]

        # Dynamically get the correct model based on location type
        Model = LOCATION_TYPE_MODELS.get(querys.location_type[i])

        if not Model:
            raise LocationNotFoundException()

        query_result = (
            db.query(
                Model.id.label('id'),
                Model.name.label('name'),
                func.st_y(Model.coord).label('latitude'),
                func.st_x(Model.coord).label('longitude'),
                (1-Model.embedding.cosine_distance(query_embeding)).label('similarity')
            )
            .filter(func.ST_Distance(
                func.ST_Transform(Model.coord, 3857),
                func.ST_Transform(current_location, 3857)
            ) < querys.distance_threshold)
            .filter((1-Model.embedding.cosine_distance(query_embeding)) > querys.similarity_threshold)
            .filter((1-Model.embedding.cosine_distance(negative_query_embeding)) < querys.negative_similarity_threshold)
            # Exclude places already seen
            .filter(Model.name.notin_(seen_places))
            .order_by(desc('similarity'))
            .limit(10)


        )

        locations = query_result.all()

        if locations:
            similarities = [result.similarity for result in locations]
            probs = softmax(similarities)

            chosen_idx = np.random.choice(len(locations), p=probs)
            chosen_location = locations[chosen_idx]

            results.append(chosen_location)
            current_location = WKTElement(
                f'POINT({chosen_location.longitude} {chosen_location.latitude})', srid=4326)
            seen_places.add(chosen_location.name)

        else:
            raise LocationNotFoundException()

        prompt_location = PROMPT_LOCATION_TYPE_MODELS.get(
            querys.location_type[i])
        insert_prompt_location = prompt_location(
            prompt_id=prompt.prompt_id,
            created_by_user_id=current_user.user_id,
            location_id=chosen_location.id
        )

        db.add(insert_prompt_location)
        db.commit()

    if results == []:
        raise LocationNotFoundException()

    # Create route
    location_names = [location.name for location in results]
    coordinates = [{"latitude": querys.latitude,
                    "longitude": querys.longitude}]
    for location in results:
        coordinates.append({"latitude": location.latitude,
                           "longitude": location.longitude})

    coordinates_str = [
        f"{c['longitude']}, {c['latitude']}" for c in coordinates]

    route = get_route(';'.join(coordinates_str), profile=querys.route_type)
    route_coordinates = route['routes'][0]['geometry']['coordinates']
    route_coordinates = [{"latitude": coord[1], "longitude": coord[0]}
                         for coord in route_coordinates]

    instructions = []
    for leg in route['routes'][0]['legs']:
        for step in leg['steps']:
            instructions.append(step['maneuver']['instruction'])

    duration = route['routes'][0]['duration']

    insert_route = models.Route(
        created_by_user_id=current_user.user_id,
        locations=location_names,
        location_latitudes=[c["latitude"] for c in coordinates],
        location_longitudes=[c["longitude"] for c in coordinates],
        route_latitudes=[c["latitude"] for c in route_coordinates],
        route_longitudes=[c["longitude"] for c in route_coordinates],
        instructions=instructions,
        duration=duration,
        created_at=prompt.created_at
    )
    db.add(insert_route)
    db.commit()
    db.refresh(insert_route)

    out = schemas.RouteOutV2.from_orm(insert_route)

    return out
