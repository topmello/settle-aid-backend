from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, func, text
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement

from sentence_transformers import SentenceTransformer

from ..database import get_db

from .. import models, schemas, oauth2

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}},
)

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Dictionary mapping location types to models
LOCATION_TYPE_MODELS = {
    "landmark": models.Landmark,
    "restaurant": models.Restaurant,
}

@router.post("/", response_model=list[schemas.SearchResult])
async def search_by_query(query: schemas.Query, db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
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