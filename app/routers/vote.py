from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models, oauth2
from ..database import get_db
import aioredis
from ..redis import get_redis_logs_db, log_to_redis

router = APIRouter(
    prefix='/vote',
    tags=["Vote"]
)


@router.post("/", status_code=201)
async def vote(
        vote: schemas.VoteIn,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user),
        r_logger: aioredis.Redis = Depends(get_redis_logs_db)
):
    await log_to_redis("Vote", f"POST request to /vote/", r_logger)
    vote_query = db.query(models.User_Route_Vote).filter(
        models.User_Route_Vote.user_id == current_user.user_id,
        models.User_Route_Vote.route_id == vote.route_id
    )
    found_vote = vote_query.first()

    if vote.vote:
        if found_vote:
            await log_to_redis("Vote", f"Already voted", r_logger)
            raise HTTPException(status_code=409, detail="Already voted")
        else:
            new_vote = models.User_Route_Vote(
                user_id=current_user.user_id,
                route_id=vote.route_id
            )
            db.add(new_vote)
            db.commit()

            await log_to_redis("Vote", f"Vote registered", r_logger)
            return {"detail": "Vote registered"}
    else:
        if not found_vote:
            await log_to_redis("Vote", f"Vote not found", r_logger)
            raise HTTPException(status_code=404, detail="Vote not found")
        else:
            vote_query.delete(synchronize_session=False)
            db.commit()

            await log_to_redis("Vote", f"Vote removed", r_logger)
            return {"detail": "Vote removed"}
