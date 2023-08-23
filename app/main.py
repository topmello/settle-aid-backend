from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from .config import settings
from .routers import auth, user, search
from .database import get_db
from . import models

import json
# Create FastAPI instance
app = FastAPI()

# Add CORS middleware need to change this later for more security
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(search.router)

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    print("Starting up...")
    prompt = "Hello World"
    embed = search.model.encode([prompt])

    with open('data/landmarks.json', 'r') as f:
        landmarks = json.load(f)
    print(type(landmarks[0]['landmark_embedding']))
    print('Inserting data')
    db = next(get_db())
    stmt = insert(models.Landmark).values(landmarks).on_conflict_do_nothing(index_elements=['landmark_id'])
    db.execute(stmt)
    db.commit()
    print('Done inserting data')
    #print(embed.shape)
    pass