from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
import aioredis
from ..common import templates
from ..database import get_db
from ..redis import get_redis_feed_db
from .. import schemas, oauth2

from .route import fetch_top_routes

router = APIRouter(
    prefix='/ui',
    tags=["UI"]
)


@router.get("/")
async def ui(request: Request):
    return templates.TemplateResponse("layout.html", {"request": request})


@router.get('/login/')
async def login_ui(request: Request):
    response = templates.TemplateResponse("login.html", {"request": request})
    return response


@router.get("/feed/")
async def dashboard_ui(request: Request,
                       order_by: str = 'num_votes',
                       offset: int = 0,
                       limit: int = 2,
                       r: aioredis.Redis = Depends(get_redis_feed_db),
                       db: Session = Depends(get_db),
                       current_user: schemas.User = Depends(oauth2.get_current_user)):

    initial_routes = await fetch_top_routes(order_by, offset, limit, r, db, current_user)

    next_offset = offset + limit
    return templates.TemplateResponse("routes.html", {"request": request, "initial_routes": initial_routes, "next_offset": next_offset})


@router.get("/feed/top_routes")
async def get_top_routes_htmx(
        request: Request,
        order_by: str = 'num_votes',
        offset: int = 0,
        limit: int = 2,
        r: aioredis.Redis = Depends(get_redis_feed_db),
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)):

    routes = await fetch_top_routes(order_by, offset, limit, r, db, current_user)

    if not routes:
        return templates.TemplateResponse("end_data.html", {"request": request})

    next_offset = offset + limit
    return templates.TemplateResponse("routes_partial.html", {"request": request, "routes": routes, "next_offset": next_offset})
