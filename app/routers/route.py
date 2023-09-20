from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from .. import schemas, models, oauth2
from ..database import get_db
from ..limiter import limiter


from ..exceptions import UserNotFoundException, RouteNotFoundException, ParametersTooLargeException

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
        db: Session = Depends(get_db)):
    """
    Retrieve route details by route ID.

    Args:
    - route_id (int): The ID of the desired route.

    Raises:
    - RouteNotFoundException: If no route is found with the specified ID.

    Returns:
    - schemas.RouteVoteOut: The route details and the number of votes.
    """

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

    try:
        route_obj, num_votes = result
    except ValueError:
        raise RouteNotFoundException()

    route_vote_out = schemas.RouteVoteOut(
        route=route_db_to_pydantic(route_obj),
        num_votes=num_votes
    )
    return route_vote_out


@router.get('/user/{user_id}/', response_model=list[schemas.RouteVoteOutUser])
@limiter.limit("5/second")
async def get_routes(
        request: Request, user_id: int,
        limit: int = 10,
        db: Session = Depends(get_db)):
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

    routes = (
        db.query(
            models.Route,
            func.count(models.User_Route_Vote.route_id),
            (func.sum(
                case((models.User_Route_Vote.user_id == user_id, 1), else_=0)
            ) > 0).label('voted_by_user')
        )
        .filter(models.Route.created_by_user_id == user_id)
        .join(models.User_Route_Vote, models.Route.route_id == models.User_Route_Vote.route_id, isouter=True)
        .group_by(models.Route.route_id)
        .order_by(models.Route.created_at.desc())
        .limit(limit)
        .all()
    )

    routes_out = [schemas.RouteVoteOutUser(
        route=route_db_to_pydantic(route_obj),
        num_votes=num_votes,
        voted_by_user=voted_by_user) for route_obj, num_votes, voted_by_user in routes]

    return routes_out


@router.get('/user/fav/{user_id}/', response_model=list[schemas.RouteVoteOutUser])
@limiter.limit("5/second")
async def get_routes(
        request: Request,
        user_id: int,
        limit: int = 10,
        db: Session = Depends(get_db)):
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

    routes = (
        db.query(
            models.Route,
            func.count(models.User_Route_Vote.route_id),
            (func.sum(
                case((models.User_Route_Vote.user_id == user_id, 1), else_=0)
            ) > 0).label('voted_by_user')
        )
        .filter(models.Route.created_by_user_id == user_id)
        .join(models.User_Route_Vote, models.Route.route_id == models.User_Route_Vote.route_id, isouter=True)
        .filter(models.User_Route_Vote.user_id == user_id)
        .group_by(models.Route.route_id)
        .order_by(models.Route.created_at.desc())
        .limit(limit)
        .all()
    )
    routes_out = [schemas.RouteVoteOutUser(
        route=route_db_to_pydantic(route_obj),
        num_votes=num_votes,
        voted_by_user=voted_by_user) for route_obj, num_votes, voted_by_user in routes]

    return routes_out
