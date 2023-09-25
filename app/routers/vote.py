from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
import aioredis
from .. import schemas, models, oauth2
from ..database import get_db
from ..redis import get_redis_feed_db, async_retry
from ..exceptions import RouteNotFoundException, AlreadyVotedException, VoteNotFoundException
router = APIRouter(
    prefix='/vote',
    tags=["Vote"]
)


@async_retry()
async def increment_route_votes_in_redis(route_id: int, r: aioredis.Redis):
    await r.zincrby('routes_feed', 1, route_id)


@async_retry()
async def decrement_route_votes_in_redis(route_id: int, r: aioredis.Redis):
    await r.zincrby('routes_feed', -1, route_id)


@router.post("/{route_id}/", status_code=201)
async def add_vote(
        route_id: int,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    """
    Allow a user to vote for a specific route.

    Args:
    - vote (schemas.VoteIn): Details of the vote, including the route to vote for.
    - Logged in required: The user must be logged in to vote.

    Raises:
    - RouteNotFoundException: If no routes are found in the database.
    - AlreadyVotedException: If the user has already voted for the specified route.

    Returns:
    - dict: A dictionary containing details of the voting action, including a type and a message.
    """

    if db.query(models.Route).filter(models.Route.route_id == route_id).first() is None:
        raise RouteNotFoundException()

    found_vote = db.query(models.User_Route_Vote).filter(
        models.User_Route_Vote.user_id == current_user.user_id,
        models.User_Route_Vote.route_id == route_id
    ).first()

    if found_vote:
        raise AlreadyVotedException()

    new_vote = models.User_Route_Vote(
        user_id=current_user.user_id,
        route_id=route_id
    )
    db.add(new_vote)
    db.commit()

    await increment_route_votes_in_redis(route_id, r)

    return {"detail": {
        "type": "voted",
        "message": "Route Favourited"
    }}


@router.delete("/{route_id}/", status_code=204)
async def delete_vote(
        route_id: int,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    """
    Allow a user to remove their vote for a specific route.

    Args:
    - vote (schemas.VoteIn): Details of the vote, including the route to un-vote for.
    - Logged in required: The user must be logged in to un-vote.

    Raises:
    - VoteNotFoundException: If the user tries to remove a vote but hasn't voted for the specified route in the first place.

    Returns:
    - dict: A dictionary containing a message.
    """
    if db.query(models.Route).filter(models.Route.route_id == route_id).first() is None:
        raise RouteNotFoundException()

    vote_query = db.query(models.User_Route_Vote).filter(
        models.User_Route_Vote.user_id == current_user.user_id,
        models.User_Route_Vote.route_id == route_id
    )
    found_vote = vote_query.first()

    if not found_vote:
        raise VoteNotFoundException()

    vote_query.delete(synchronize_session=False)
    db.commit()

    await decrement_route_votes_in_redis(route_id, r)

    return {"detail": {
        "type": "unvoted",
        "message": "Route Unfavourited"
    }}
