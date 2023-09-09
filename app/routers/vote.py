from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models, oauth2
from ..database import get_db

router = APIRouter(
    prefix='/vote',
    tags=["Vote"]
)


@router.post("/", status_code=201)
def vote(
        vote: schemas.VoteIn,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):

    vote_query = db.query(models.User_Route_Vote).filter(
        models.User_Route_Vote.user_id == current_user.user_id,
        models.User_Route_Vote.route_id == vote.route_id
    )
    found_vote = vote_query.first()

    if vote.vote:
        if found_vote:
            raise HTTPException(status_code=409, detail="Already voted")
        else:
            new_vote = models.User_Route_Vote(
                user_id=current_user.user_id,
                route_id=vote.route_id
            )
            db.add(new_vote)
            db.commit()

            return {"detail": "Vote registered"}
    else:
        if not found_vote:
            raise HTTPException(status_code=404, detail="Vote not found")
        else:
            vote_query.delete(synchronize_session=False)
            db.commit()

            return {"detail": "Vote removed"}
