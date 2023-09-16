from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from .. import schemas, models, oauth2
from ..database import get_db
from ..exceptions import RouteNotFoundException, AlreadyVotedException, VoteNotFoundException
router = APIRouter(
    prefix='/vote',
    tags=["Vote"]
)


@router.post("/", status_code=201)
async def vote(
        vote: schemas.VoteIn,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    """
    Allow a user to vote or remove their vote for a specific route.

    Args:
    - vote (schemas.VoteIn): Details of the vote, including the route to vote for and the voting action (vote or un-vote) as boolean.
    - Logged in required: The user must be logged in to vote.

    Raises:
    - RouteNotFoundException: If no routes are found in the database.
    - AlreadyVotedException: If the user has already voted for the specified route and is trying to vote again.
    - VoteNotFoundException: If the user tries to remove a vote but hasn't voted for the specified route in the first place.

    Returns:
    - dict: A dictionary containing details of the voting action, including a type (if voted) and a message.
    """

    if db.query(func.count(models.Route.route_id)).scalar() == 0:
        raise RouteNotFoundException()

    vote_query = db.query(models.User_Route_Vote).filter(
        models.User_Route_Vote.user_id == current_user.user_id,
        models.User_Route_Vote.route_id == vote.route_id
    )
    found_vote = vote_query.first()

    if vote.vote:
        if found_vote:
            raise AlreadyVotedException()
        else:
            new_vote = models.User_Route_Vote(
                user_id=current_user.user_id,
                route_id=vote.route_id
            )
            db.add(new_vote)
            db.commit()

            return {"detail": {
                "type": "voted",
                "message": "Vote added"
            }}
    else:
        if not found_vote:
            raise VoteNotFoundException()
        else:
            vote_query.delete(synchronize_session=False)
            db.commit()

            return {"detail": "Vote removed"}
