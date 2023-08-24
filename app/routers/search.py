from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session

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

@router.get("/", response_model=list[schemas.SearchResult])
async def search_by_prompt(query: schemas.Query, db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    query_embeding = model.encode([query.query])[0]

    location = query.location_type

    # Dynamically get the correct model based on location type
    Model = LOCATION_TYPE_MODELS.get(location)

    if not Model:
        raise HTTPException(status_code=404, detail="Location type not found")

    query_result = (
        db.query(
        Model.name.label('name'),
        func.st_y(Model.coord).label('latitude'),
        func.st_x(Model.coord).label('longitude'),
        (1-Model.embedding.cosine_distance(query_embeding)).label('similarity')
        )
        .order_by(desc('similarity'))
        .limit(10)
    )
    print(query_result.all())

    # Place holder for now
    return query_result.all()