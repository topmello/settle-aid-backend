from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, case
import aioredis

from .. import schemas, models, oauth2
from ..database import get_db
from ..limiter import limiter
from ..redis import get_redis_cache_db

from ..exceptions import UserNotFoundException, RouteNotFoundException, ParametersTooLargeException, NotAuthorisedException

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
        r: aioredis.Redis = Depends(get_redis_cache_db)):
    """
    Retrieve route details by route ID.

    Args:
    - route_id (int): The ID of the desired route.

    Raises:
    - RouteNotFoundException: If no route is found with the specified ID.

    Returns:
    - schemas.RouteVoteOut: The route details and the number of votes.
    """

    cached_data = await r.get(f"route:{route_id}")
    if cached_data:
        # Deserialize cached data
        route_vote_out = schemas.RouteVoteOut.parse_raw(cached_data)
        return route_vote_out

    if db.query(func.count(models.Route.route_id)).scalar() == 0:
        raise RouteNotFoundException()

    route_query = (
        db.query(
            models.Route,
            func.count(models.User_Route_Vote.route_id)
        ).filter(
            models.Route.route_id == route_id)
        .join(models.User_Route_Vote, models.Route.route_id == models.User_Route_Vote.route_id, isouter=True)
        .group_by(models.Route.route_id)
    )

    result = route_query.first()

    if result is None:
        raise RouteNotFoundException()

    route_obj, num_votes = result

    route_vote_out = schemas.RouteVoteOut(
        route=route_db_to_pydantic(route_obj),
        num_votes=num_votes
    )

    await r.set(f"route:{route_id}", route_vote_out.json(), ex=60)

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
        r: aioredis.Redis = Depends(get_redis_cache_db)):
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

    if limit > 50:
        raise ParametersTooLargeException()

    if db.query(models.User).filter(models.User.user_id == user_id).first() is None:
        raise UserNotFoundException()

    if db.query(func.count(models.Route.route_id)).scalar() == 0:
        raise RouteNotFoundException()

    route_ids = (
        db.query(models.Route.route_id)
        .filter(models.Route.created_by_user_id == user_id)
        .order_by(models.Route.created_at.desc())
        .limit(limit)
        .all()
    )
    route_ids = [r[0] for r in route_ids]  # Flatten the list

    routes_out = []
    cached_routes = await r.mget(*[f"route_voted:{route_id}" for route_id in route_ids])

    not_cached_route_ids = []
    routes_out_cached = []

    for idx, cached_route in enumerate(cached_routes):
        if cached_route is not None:
            route_vote_out = schemas.RouteVoteOutUser.parse_raw(cached_route)
            routes_out_cached.append(route_vote_out)

        else:
            not_cached_route_ids.append(route_ids[idx])

    routes = (
        db.query(
            models.Route,
            func.count(models.User_Route_Vote.route_id),
            (func.sum(
                case((models.User_Route_Vote.user_id == user_id, 1), else_=0)
            ) > 0).label('voted_by_user')
        )
        .filter(models.Route.route_id.in_(not_cached_route_ids))
        .join(models.User_Route_Vote, models.Route.route_id == models.User_Route_Vote.route_id, isouter=True)
        .group_by(models.Route.route_id)
        .order_by(models.Route.created_at.desc())
        .limit(limit)
        .all()
    )

    routes_out_fresh = []
    for route_obj, num_votes, voted_by_user in routes:
        route_vote_out = schemas.RouteVoteOutUser(
            route=route_db_to_pydantic(route_obj),
            num_votes=num_votes,
            voted_by_user=voted_by_user
        )
        await r.set(f"route_voted:{route_obj.route_id}", route_vote_out.json(), ex=60)
        routes_out_fresh.append(route_vote_out)

    combined_routes = routes_out_fresh + routes_out_cached
    sorted_routes = sorted(
        combined_routes, key=lambda x: x.route.route_id, reverse=True)

    return sorted_routes


@router.get('/user/fav/{user_id}/', response_model=list[schemas.RouteVoteOutUser])
@limiter.limit("5/second")
async def get_routes(
        request: Request,
        user_id: int,
        limit: int = 10,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_cache_db)):
    """
    Retrieve a list of favorite routes of a specified user.

    Args:
    - user_id (int): The ID of the user whose favorite routes are to be retrieved.
    - limit (int): The maximum number of favorite routes to retrieve. Defaults to 10.

    Raises:
    - ParametersTooLargeException: If the limit specified exceeds 50.
    - UserNotFoundException: If no user is found with the specified ID.
    - RouteNotFoundException: If no routes are found.

    Returns:
    - List[schemas.RouteVoteOut]: A list of favorite routes and their respective vote counts.


    """

    if limit > 50:
        raise ParametersTooLargeException()

    if db.query(models.User).filter(models.User.user_id == user_id).first() is None:
        raise UserNotFoundException()

    if db.query(func.count(models.Route.route_id)).scalar() == 0:
        raise RouteNotFoundException()

    route_ids = (
        db.query(models.Route.route_id)
        .join(models.User_Route_Vote, models.Route.route_id == models.User_Route_Vote.route_id)
        .filter(models.User_Route_Vote.user_id == user_id)
        .order_by(models.Route.created_at.desc())
        .limit(limit)
        .all()
    )
    route_ids = [r[0] for r in route_ids]  # Flatten the list

    routes_out = []
    cached_routes = await r.mget(*[f"route_voted:{route_id}" for route_id in route_ids])

    not_cached_route_ids = []
    routes_out_cached = []

    for idx, cached_route in enumerate(cached_routes):
        if cached_route is not None:
            route_vote_out = schemas.RouteVoteOutUser.parse_raw(cached_route)
            if route_vote_out.voted_by_user:
                routes_out_cached.append(route_vote_out)
        else:
            not_cached_route_ids.append(route_ids[idx])

    routes = (
        db.query(
            models.Route,
            func.count(models.User_Route_Vote.route_id),
            (func.sum(
                case((models.User_Route_Vote.user_id == user_id, 1), else_=0)
            ) > 0).label('voted_by_user')
        )
        .filter(models.Route.route_id.in_(not_cached_route_ids))
        .join(models.User_Route_Vote, models.Route.route_id == models.User_Route_Vote.route_id, isouter=True)
        .filter(models.User_Route_Vote.user_id == user_id)
        .group_by(models.Route.route_id)
        .order_by(models.Route.created_at.desc())
        .limit(limit)
        .all()
    )

    routes_out_fresh = []
    for route_obj, num_votes, voted_by_user in routes:
        route_vote_out = schemas.RouteVoteOutUser(
            route=route_db_to_pydantic(route_obj),
            num_votes=num_votes,
            voted_by_user=voted_by_user
        )
        await r.set(f"route_voted:{route_obj.route_id}", route_vote_out.json(), ex=60)
        routes_out_fresh.append(route_vote_out)

    combined_routes = routes_out_fresh + routes_out_cached
    sorted_routes = sorted(
        combined_routes, key=lambda x: x.route.route_id, reverse=True)

    return sorted_routes
