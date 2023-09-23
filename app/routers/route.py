from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc
import aioredis
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
import json

from .. import schemas, models, oauth2
from ..database import get_db
from ..redis import get_redis_feed_db, async_retry
from ..limiter import limiter


from ..exceptions import UserNotFoundException, RouteNotFoundException, ParametersTooLargeException, NotAuthorisedException, InvalidSearchQueryException

router = APIRouter(
    prefix='/route',
    tags=["Route"]
)


def datetime_serializer(o):
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError("Object not serializable")


async def get_route_from_redis_or_db(route_id, r: aioredis.Redis, db: Session) -> schemas.RouteOutV2:
    # Try fetching route from Redis first
    route_data = await r.get(f"route_details_{route_id}")

    if route_data:
        # If found in Redis, deserialize it to a Python object
        route_obj = json.loads(route_data)
        route_obj = schemas.RouteOutV2(**route_obj)
    else:
        # If not found in Redis, fetch from the DB
        route_obj = db.query(models.Route).filter(
            models.Route.route_id == route_id).first()
        route_obj = schemas.RouteOutV2.from_orm(route_obj)

        # Store in Redis for future use
        # 1 hour expiration
        await r.set(f"route_details_{route_id}", json.dumps(route_obj.model_dump(), default=datetime_serializer), ex=3600)

    return route_obj


def merge_route_details(
        route_objects: List[schemas.RouteOutV2],
        vote_details: List[Tuple[int, int, bool]]) -> List[schemas.RouteVoteOutUser]:
    """
    Merge route objects with their vote details.
    """
    # Convert vote details into a dictionary for quick lookup
    vote_dict = {route_id: (num_votes, voted_by_user)
                 for route_id, num_votes, voted_by_user in vote_details}

    merged_results = []
    for route_obj in route_objects:
        route_id = route_obj.route_id
        # Default to 0 votes and not voted by user
        num_votes, voted_by_user = vote_dict.get(route_id, (0, False))

        merge_result = schemas.RouteVoteOutUser(
            route=route_obj,
            num_votes=num_votes,
            voted_by_user=voted_by_user
        )

        merged_results.append(merge_result)

    return merged_results


@router.get('/{route_id}', response_model=schemas.RouteVoteOut)
@limiter.limit("1/second")
async def get_route(
        request: Request,
        route_id: int,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db)):
    """
    Retrieve route details by route ID.

    Args:
    - route_id (int): The ID of the desired route.

    Raises:
    - RouteNotFoundException: If no route is found with the specified ID.

    Returns:
    - schemas.RouteVoteOut: The route details and the number of votes.
    """

    route_obj = await get_route_from_redis_or_db(route_id, r, db)

    if not route_obj:
        raise RouteNotFoundException()

    num_votes = (
        db.query(func.count(models.User_Route_Vote.route_id))
        .filter(models.User_Route_Vote.route_id == route_id)
        .scalar()
    )

    route_vote_out = schemas.RouteVoteOut(
        route=route_obj,
        num_votes=num_votes
    )

    return route_vote_out


@router.delete('/{route_id}', status_code=204)
@limiter.limit("1/second")
async def delete_route(
        request: Request,
        route_id: int,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)):
    """
    Delete a route by its ID.

    Args:
    - route_id (int): The ID of the route to delete.

    Raises:
    - RouteNotFoundException: If no route is found with the specified ID.
    - PermissionDeniedException: If the route does not belong to the current user.
    """

    route_query = db.query(models.Route).filter(
        models.Route.route_id == route_id)
    route_to_delete = route_query.first()

    if not route_to_delete:
        raise RouteNotFoundException()

    # Check if the route belongs to the current user
    if route_to_delete.created_by_user_id != current_user.user_id:
        raise NotAuthorisedException()

    # Delete associated votes
    db.query(models.User_Route_Vote).filter(
        models.User_Route_Vote.route_id == route_id).delete()

    # Delete the route
    route_query.delete()
    db.commit()

    return Response(status_code=204)


@router.get('/user/{user_id}/', response_model=list[schemas.RouteVoteOutUser])
@limiter.limit("5/second")
async def get_routes(
        request: Request, user_id: int,
        limit: int = 10,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)):
    """
    Retrieve a list of routes created by a specified user.

    Args:
    - user_id (int): The ID of the user whose routes are to be retrieved.
    - limit (int): The maximum number of routes to retrieve. Defaults to 10.

    Raises:
    - ParametersTooLargeException: If the limit specified exceeds 50.
    - UserNotFoundException: If no user is found with the specified ID.
    - RouteNotFoundException: If no routes are found.

    Returns:
    - List[schemas.RouteVoteOut]: A list of routes and their respective vote counts.
    """

    if current_user.user_id != user_id:
        raise NotAuthorisedException()

    if limit > 50:
        raise ParametersTooLargeException()

    if db.query(models.User).filter(models.User.user_id == user_id).first() is None:
        raise UserNotFoundException()

    route_ids = (
        db.query(models.Route.route_id)
        .filter(models.Route.created_by_user_id == user_id)
        .order_by(models.Route.created_at.desc())
        .limit(limit)
        .all()
    )

    if not route_ids:
        raise RouteNotFoundException()

    route_ids = [route_id[0] for route_id in route_ids]

    route_objects = [
        await get_route_from_redis_or_db(route_id, r, db)
        for route_id in route_ids
    ]

    vote_details = (
        db.query(
            models.User_Route_Vote.route_id,
            func.count(models.User_Route_Vote.route_id).label("num_votes"),
            (func.sum(case((models.User_Route_Vote.user_id ==
             current_user.user_id, 1), else_=0)) > 0).label('voted_by_user')
        )
        .filter(models.User_Route_Vote.route_id.in_(route_ids))
        .group_by(models.User_Route_Vote.route_id)
        .all()
    )

    routes_out = merge_route_details(
        route_objects=route_objects, vote_details=vote_details)

    return routes_out


@router.get('/user/fav/{user_id}/', response_model=list[schemas.RouteVoteOutUser])
@limiter.limit("5/second")
async def get_routes(
        request: Request, user_id: int,
        limit: int = 10,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)):
    """
    Retrieve a list of routes created by a specified user.

    Args:
    - user_id (int): The ID of the user whose routes are to be retrieved.
    - limit (int): The maximum number of routes to retrieve. Defaults to 10.

    Raises:
    - ParametersTooLargeException: If the limit specified exceeds 50.
    - UserNotFoundException: If no user is found with the specified ID.
    - RouteNotFoundException: If no routes are found.

    Returns:
    - List[schemas.RouteVoteOut]: A list of routes and their respective vote counts.
    """

    if current_user.user_id != user_id:
        raise NotAuthorisedException()

    if limit > 50:
        raise ParametersTooLargeException()

    if db.query(models.User).filter(models.User.user_id == user_id).first() is None:
        raise UserNotFoundException()

    route_ids = (
        db.query(models.User_Route_Vote.route_id)
        .filter(models.User_Route_Vote.user_id == user_id)
        .join(models.Route, models.Route.route_id == models.User_Route_Vote.route_id)
        .filter(models.Route.created_by_user_id == user_id)
        .order_by(models.Route.created_at.desc())
        .limit(limit)
        .all()
    )

    if not route_ids:
        raise RouteNotFoundException()

    route_ids = [route_id[0] for route_id in route_ids]

    route_objects = [
        await get_route_from_redis_or_db(route_id, r, db)
        for route_id in route_ids
    ]

    vote_details = (
        db.query(
            models.User_Route_Vote.route_id,
            func.count(models.User_Route_Vote.route_id).label("num_votes"),
            (func.sum(case((models.User_Route_Vote.user_id ==
             current_user.user_id, 1), else_=0)) > 0).label('voted_by_user')
        )
        .filter(models.User_Route_Vote.route_id.in_(route_ids))
        .group_by(models.User_Route_Vote.route_id)
        .all()
    )

    routes_out = merge_route_details(
        route_objects=route_objects, vote_details=vote_details)

    return routes_out


@router.get('/feed/user/fav/{user_id}/', response_model=list[schemas.RouteVoteOutUser])
@limiter.limit("5/second")
async def get_routes(
        request: Request, user_id: int,
        limit: int = 10,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)):
    """
    Retrieve a list of routes created by a specified user.

    Args:
    - user_id (int): The ID of the user whose routes are to be retrieved.
    - limit (int): The maximum number of routes to retrieve. Defaults to 10.

    Raises:
    - ParametersTooLargeException: If the limit specified exceeds 50.
    - UserNotFoundException: If no user is found with the specified ID.
    - RouteNotFoundException: If no routes are found.

    Returns:
    - List[schemas.RouteVoteOut]: A list of routes and their respective vote counts.
    """

    if current_user.user_id != user_id:
        raise NotAuthorisedException()

    if limit > 50:
        raise ParametersTooLargeException()

    if db.query(models.User).filter(models.User.user_id == user_id).first() is None:
        raise UserNotFoundException()

    route_ids = (
        db.query(models.User_Route_Vote.route_id)
        .filter(models.User_Route_Vote.user_id == user_id)
        .join(models.Route, models.Route.route_id == models.User_Route_Vote.route_id)
        .order_by(models.Route.created_at.desc())
        .limit(limit)
        .all()
    )

    if not route_ids:
        raise RouteNotFoundException()

    route_ids = [route_id[0] for route_id in route_ids]

    route_objects = [
        await get_route_from_redis_or_db(route_id, r, db)
        for route_id in route_ids
    ]

    vote_details = (
        db.query(
            models.User_Route_Vote.route_id,
            func.count(models.User_Route_Vote.route_id).label("num_votes"),
            (func.sum(case((models.User_Route_Vote.user_id ==
             current_user.user_id, 1), else_=0)) > 0).label('voted_by_user')
        )
        .filter(models.User_Route_Vote.route_id.in_(route_ids))
        .group_by(models.User_Route_Vote.route_id)
        .all()
    )

    routes_out = merge_route_details(
        route_objects=route_objects, vote_details=vote_details)

    return routes_out


@async_retry()
async def publish_route_in_redis(route_id: int, r: aioredis.Redis, db: Session):

    num_votes = db.query(func.count(models.User_Route_Vote.route_id)).filter(
        models.User_Route_Vote.route_id == route_id).scalar()

    # Add the route to the ZSET with a score of 0
    await r.zadd('routes_feed', {route_id: num_votes})
    # Set a separate expiration key for the route
    # 86400 seconds = 1 day
    await r.setex(f"route_expiry:{route_id}", 86400, 'expire')


@async_retry()
async def cleanup_expired_routes(r: aioredis.Redis):
    # Get all routes from ZSET
    route_ids = await r.zrange('routes_feed', 0, -1)
    for route_id in route_ids:
        # If the expiration key doesn't exist, remove the route from ZSET
        if not await r.exists(f"route_expiry:{route_id}"):
            await r.zrem('routes_feed', route_id)


@router.post("/publish/{route_id}", status_code=201)
async def publish_route(
        request: Request,
        route_id: int,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)):
    """
    Publish a route to the feed.
    """
    # Check if route exists
    if db.query(models.Route).filter(models.Route.route_id == route_id).first() is None:
        raise RouteNotFoundException()

    # Check if the route belongs to the current user
    route = db.query(models.Route).filter(
        models.Route.route_id == route_id).first()
    if route.created_by_user_id != current_user.user_id:
        raise NotAuthorisedException()

    # Publish the route in Redis
    await publish_route_in_redis(route_id, r, db)

    return {"detail": {
        "type": "published",
        "message": "Route Published"
    }}


@router.get("/feed/top_routes", response_model=list[schemas.RouteVoteOutUser])
async def get_top_routes(
        request: Request,
        order_by: str = 'num_votes',
        limit: int = 10,
        offset: int = 0,
        r: aioredis.Redis = Depends(get_redis_feed_db),
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)):
    """
    Get top routes sorted by votes.
    """
    # First, clean up expired routes
    await cleanup_expired_routes(r)

    order_by_options = ['created_at', 'num_votes']
    if order_by not in order_by_options:
        raise InvalidSearchQueryException()

    # Then, fetch top routes from Redis
    route_ids_with_votes = await r.zrevrange('routes_feed', offset, offset+limit-1, withscores=True)
    route_ids = [route[0] for route in route_ids_with_votes]

    route_objects = [await get_route_from_redis_or_db(route_id, r, db) for route_id in route_ids]

    # Query DB for route details based on IDs
    vote_details = (
        db.query(
            models.User_Route_Vote.route_id,
            func.count(models.User_Route_Vote.route_id).label("num_votes"),
            (func.sum(case((models.User_Route_Vote.user_id ==
             current_user.user_id, 1), else_=0)) > 0).label('voted_by_user')
        )
        .filter(models.User_Route_Vote.route_id.in_(route_ids))
        .group_by(models.User_Route_Vote.route_id)
        .all()
    )

    routes_out = merge_route_details(
        route_objects=route_objects, vote_details=vote_details)

    return routes_out
