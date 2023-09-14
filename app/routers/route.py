from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import schemas, models, oauth2
from ..database import get_db
from ..limiter import limiter

import aioredis
from ..redis import get_redis_logs_db, log_to_redis

router = APIRouter(
    prefix='/route',
    tags=["Route"]
)


def route_db_to_pydantic(route_db: models.Route) -> schemas.RouteOutV2:

    # Extract locations_coordinates
    locations_coordinates = [
        {"latitude": lat, "longitude": long} for lat, long in zip(route_db.location_latitudes, route_db.location_longitudes)
    ]

    # Extract route
    route = [
        {"latitude": lat, "longitude": long} for lat, long in zip(route_db.route_latitudes, route_db.route_longitudes)
    ]
    return schemas.RouteOutV2(
        route_id=route_db.route_id,
        locations=route_db.locations,
        locations_coordinates=locations_coordinates,
        route=route,
        instructions=route_db.instructions,
        duration=float(route_db.duration)
    )


@router.get('/{route_id}', response_model=schemas.RouteVoteOut)
@limiter.limit("1/second")
async def get_route(
        request: Request,
        route_id: int,
        db: Session = Depends(get_db),
        r_logger: aioredis.Redis = Depends(get_redis_logs_db)):

    await log_to_redis("Route", f"{request.method} request to {request.url.path}", r_logger)
    route_query = (
        db.query(models.Route, func.count(models.User_Route_Vote.route_id)).filter(
            models.Route.route_id == route_id)
        .join(models.User_Route_Vote, models.Route.route_id == models.User_Route_Vote.route_id, isouter=True)
        .group_by(models.Route.route_id)
    )

    result = route_query.first()

    if not result:
        await log_to_redis("Route", f"Route not found", r_logger)
        raise HTTPException(status_code=404, detail="Route not found")

    try:
        route_obj, num_votes = result
    except ValueError:
        await log_to_redis("Route", f"Route not found", r_logger)
        raise HTTPException(status_code=404, detail="Route not found")

    route_vote_out = schemas.RouteVoteOut(
        route=route_db_to_pydantic(route_obj),
        num_votes=num_votes
    )
    await log_to_redis("Route", f"Route found", r_logger)
    return route_vote_out


@router.get('/user/{user_id}/', response_model=list[schemas.RouteVoteOut])
@limiter.limit("5/second")
async def get_routes(
        request: Request, user_id: int,
        limit: int = 10, db:
        Session = Depends(get_db),
        r_logger: aioredis.Redis = Depends(get_redis_logs_db)):
    await log_to_redis("Route", f"{request.method} request to {request.url.path}", r_logger)
    if limit > 50:
        await log_to_redis("Route", f"Limit too high", r_logger)
        raise HTTPException(status_code=400, detail="Limit too high")

    if db.query(models.User).filter(models.User.user_id == user_id).first() is None:
        await log_to_redis("Route", f"User not found", r_logger)
        raise HTTPException(status_code=404, detail="User not found")

    if db.query(func.count(models.Route.route_id)).scalar() == 0:
        await log_to_redis("Route", f"No routes found", r_logger)
        raise HTTPException(status_code=404, detail="No routes found")

    routes = (
        db.query(models.Route, func.count(models.User_Route_Vote.route_id))
        .filter(models.Route.created_by_user_id == user_id)
        .join(models.User_Route_Vote, models.Route.route_id == models.User_Route_Vote.route_id, isouter=True)
        .group_by(models.Route.route_id)
        .order_by(models.Route.created_at.desc())
        .limit(limit)
        .all()
    )
    routes_out = [schemas.RouteVoteOut(
        route=route_db_to_pydantic(route_obj),
        num_votes=num_votes) for route_obj, num_votes in routes]
    await log_to_redis("Route", f"Routes found", r_logger)
    return routes_out


@router.get('/user/fav/{user_id}/', response_model=list[schemas.RouteVoteOut])
@limiter.limit("5/second")
async def get_routes(
        request: Request,
        user_id: int,
        limit: int = 10,
        db: Session = Depends(get_db),
        r_logger: aioredis.Redis = Depends(get_redis_logs_db)):

    await log_to_redis("Route", f"{request.method} request to {request.url.path}", r_logger)

    if limit > 50:
        await log_to_redis("Route", f"Limit too high", r_logger)
        raise HTTPException(status_code=400, detail="Limit too high")

    if db.query(models.User).filter(models.User.user_id == user_id).first() is None:
        await log_to_redis("Route", f"User not found", r_logger)
        raise HTTPException(status_code=404, detail="User not found")

    if db.query(func.count(models.Route.route_id)).scalar() == 0:
        await log_to_redis("Route", f"No routes found", r_logger)
        raise HTTPException(status_code=404, detail="No routes found")

    routes = (
        db.query(models.Route, func.count(models.User_Route_Vote.route_id))
        .filter(models.Route.created_by_user_id == user_id)
        .join(models.User_Route_Vote, models.Route.route_id == models.User_Route_Vote.route_id, isouter=True)
        .filter(models.User_Route_Vote.user_id == user_id)
        .group_by(models.Route.route_id)
        .order_by(models.Route.created_at.desc())
        .limit(limit)
        .all()
    )
    routes_out = [schemas.RouteVoteOut(
        route=route_db_to_pydantic(route_obj),
        num_votes=num_votes) for route_obj, num_votes in routes]
    await log_to_redis("Route", f"Routes found", r_logger)
    return routes_out
