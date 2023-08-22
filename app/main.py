from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import auth, user, search

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
    #print(embed.shape)
    pass