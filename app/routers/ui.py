from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import aioredis
import folium
import tempfile
from pathlib import Path
from ..common import templates
from ..database import get_db
from ..redis import get_redis_feed_db
from .. import schemas, oauth2

from .route import fetch_top_routes, get_routes_, get_route_
from .search import search_by_query_seq_v2_

router = APIRouter(
    prefix='/ui',
    tags=["UI"]
)


@router.get("/")
async def ui(request: Request):
    return templates.TemplateResponse("layout.html", {"request": request})


@router.get("/prompts_input/")
async def prompts_input(request: Request):
    return templates.TemplateResponse("prompts_input.html", {"request": request})


@router.get('/login/')
async def login_ui(request: Request):
    response = templates.TemplateResponse("login.html", {"request": request})
    return response


@router.get("/feed/")
async def dashboard_ui(
        request: Request,
        query_type: str = 'top_routes',
        order_by: str = 'num_votes',
        offset: int = 0,
        limit: int = 2,
        r: aioredis.Redis = Depends(get_redis_feed_db),
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)):

    if query_type == 'top_routes':
        initial_routes = await fetch_top_routes(order_by, offset, limit, r, db, current_user)
    elif query_type == 'user_routes':
        initial_routes = await get_routes_("all", current_user.user_id, offset, limit, db, r, current_user)
    elif query_type == 'user_routes_fav':
        initial_routes = await get_routes_("fav", current_user.user_id, offset, limit, db, r, current_user)
    elif query_type == 'user_feed_fav':
        initial_routes = await get_routes_("feed_fav", current_user.user_id, offset, limit, db, r, current_user)
    else:
        return templates.TemplateResponse("end_data.html", {"request": request})

    if not initial_routes:
        return templates.TemplateResponse("end_data.html", {"request": request})

    next_offset = offset + limit
    return templates.TemplateResponse("routes.html", {"request": request, "initial_routes": initial_routes, "next_offset": next_offset})


@router.get("/feed/top_routes/")
async def get_top_routes_htmx(
        request: Request,
        query_type: str = 'top_routes',
        order_by: str = 'num_votes',
        offset: int = 0,
        limit: int = 2,
        r: aioredis.Redis = Depends(get_redis_feed_db),
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)):

    if query_type == 'top_routes':
        routes = await fetch_top_routes(order_by, offset, limit, r, db, current_user)
    elif query_type == 'user_routes':
        routes = await get_routes_("all", current_user.user_id, offset, limit, db, r, current_user)
    elif query_type == 'user_routes_fav':
        routes = await get_routes_("fav", current_user.user_id, offset, limit, db, r, current_user)
    elif query_type == 'user_feed_fav':
        routes = await get_routes_("feed_fav", current_user.user_id, offset, limit, db, r, current_user)
    else:
        return templates.TemplateResponse("end_data.html", {"request": request})

    if not routes:
        return templates.TemplateResponse("end_data.html", {"request": request})

    next_offset = offset + limit
    return templates.TemplateResponse("routes_partial.html", {"request": request, "routes": routes, "next_offset": next_offset})


async def create_map(route: schemas.RouteOutV2):
    # Accessing route_coordinates from route_out object
    route_coordinates = route.route

    # Create the folium map
    # Accessing latitude and longitude from the first coordinate
    m = folium.Map(location=[route_coordinates[0]['latitude'],
                             route_coordinates[0]['longitude']], zoom_start=15)

    # Adding PolyLine to the map
    # Accessing latitude and longitude from each coordinate
    folium.PolyLine(locations=[[coord['latitude'], coord['longitude']]
                    for coord in route_coordinates], color="blue").add_to(m)

    # Adding start marker to the map
    folium.Marker(location=[route_coordinates[0]['latitude'], route_coordinates[0]['longitude']],
                  popup='Start', icon=folium.Icon(color='green')).add_to(m)

    # Adding end marker to the map
    folium.Marker(location=[route_coordinates[-1]['latitude'], route_coordinates[-1]['longitude']],
                  popup='End', icon=folium.Icon(color='red')).add_to(m)

    # Define the path to the HTML file
    temp_dir = tempfile.TemporaryDirectory()
    map_file = Path(temp_dir.name) / "route_map.html"

    # Save the map as an HTML file
    m.save(map_file)

    # Read the HTML file and return it as a response
    with open(map_file, "r") as f:
        html = f.read()

    html = html.replace(
        '<div class="folium-map"',
        '<div class="folium-map" style="height: 400px; width: 100%; z-index: 1; border-radius: 15px;"'
    )

    temp_dir.cleanup()

    return HTMLResponse(content=html)


@router.post("/search/map/")
async def search_by_query_seq_v2_map(
        request: Request,
        querys: schemas.RouteQueryV2,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    route = await search_by_query_seq_v2_(querys, db, current_user)

    return await create_map(route)


@router.get("/route/map/{route_id}/")
async def get_route_map(
        request: Request,
        route_id: int,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    route = await get_route_(route_id, db, r)

    return await create_map(route.route)
