from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, func, text
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement

import numpy as np
from sentence_transformers import SentenceTransformer

from ..database import get_db

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

def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)

@router.post("/", response_model=list[schemas.SearchResult])
async def search_by_query(query: schemas.Query, db: Session = Depends(get_db)):
    query_embeding = model.encode([query.query])[0]

    current_location = WKTElement(f'POINT({query.longitude} {query.latitude})', srid=4326)


    # Dynamically get the correct model based on location type
    Model = LOCATION_TYPE_MODELS.get(query.location_type)

    if not Model:
        raise HTTPException(status_code=404, detail="Location type not found")

    query_result = (
        db.query(
        Model.name.label('name'),
        func.st_y(Model.coord).label('latitude'),
        func.st_x(Model.coord).label('longitude'),
        (1-Model.embedding.cosine_distance(query_embeding)).label('similarity')
        )
        .filter(func.ST_Distance(
            func.ST_Transform(Model.coord, 3857), 
            func.ST_Transform(current_location, 3857)
            ) < query.distance_threshold)
        .filter((1-Model.embedding.cosine_distance(query_embeding)) > query.similarity_threshold)
        .order_by(desc('similarity'))
        .limit(10)
    )

    if query_result.all() == []:
        raise HTTPException(status_code=404, detail="No results found")

    # Place holder for now
    return query_result.all()

@router.post("/seq/", response_model=list[schemas.SearchResult])
async def search_by_query_seq(querys: schemas.QuerySeq, db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):

    results = []
    seen_places = set()

    current_location = WKTElement(f'POINT({querys.longitude} {querys.latitude})', srid=4326)

    for i, query in enumerate(querys.query):
        query_embeding = model.encode([query])[0]

        
        prompt = models.Prompt(
            created_by_user_id=current_user.user_id,
            prompt=query,
            prompt_embeding=query_embeding,
            location_type=querys.location_type[i]
            )
        db.add(prompt)
        db.commit()


        # Dynamically get the correct model based on location type
        Model = LOCATION_TYPE_MODELS.get(querys.location_type[i])

        if not Model:
            raise HTTPException(status_code=404, detail="Location type not found")

        query_result = (
            db.query(
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
            .filter(Model.name.notin_(seen_places))  # Exclude places already seen
            .order_by(desc('similarity'))
            
        )

        location = query_result.first()
        if location:
            
            results.append(location)
            current_location = WKTElement(f'POINT({location.longitude} {location.latitude})', srid=4326)
            seen_places.add(location.name)

        else:
            raise HTTPException(status_code=404, detail="No results found")

        

    if results == []:
        raise HTTPException(status_code=404, detail="No results found")

    return results

@router.post("/seq-sample/", response_model=list[schemas.SearchResult])
async def search_by_query_seq(querys: schemas.QuerySeq, db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):

    results = []
    seen_places = set()

    current_location = WKTElement(f'POINT({querys.longitude} {querys.latitude})', srid=4326)

    for i, query in enumerate(querys.query):
        query_embeding = model.encode([query])[0]

        prompt = models.Prompt(
            created_by_user_id=current_user.user_id,
            prompt=query,
            prompt_embeding=query_embeding,
            location_type=querys.location_type[i]
            )
        db.add(prompt)
        db.commit()

        # Dynamically get the correct model based on location type
        Model = LOCATION_TYPE_MODELS.get(querys.location_type[i])

        if not Model:
            raise HTTPException(status_code=404, detail="Location type not found")

        query_result = (
            db.query(
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
            .filter(Model.name.notin_(seen_places))  # Exclude places already seen
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
            current_location = WKTElement(f'POINT({chosen_location.longitude} {chosen_location.latitude})', srid=4326)
            seen_places.add(chosen_location.name)

        else:
            raise HTTPException(status_code=404, detail="No results found")

        

    if results == []:
        raise HTTPException(status_code=404, detail="No results found")

    return results