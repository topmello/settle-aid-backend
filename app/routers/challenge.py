from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
import aioredis
from datetime import datetime, timedelta
from typing import Callable

from .. import schemas, models, oauth2
from ..database import get_db
from ..redis import get_redis_feed_db, async_retry
from ..exceptions import NotAuthorisedException


router = APIRouter(
    prefix='/challenge',
    tags=["Challenge"]
)


@router.get("/")
async def get_all_challenge_spec(db: Session = Depends(get_db)):
    query = db.query(models.Challenge).all()
    return query


async def get_leaderboard_(
    limit: int,
    r: aioredis.Redis
):
    current_date = datetime.now()
    year, week_num = current_date.isocalendar()[0:2]

    # Fetch top users from Redis for the current week
    key = f'challenge_leaderboard_score:{year}:{week_num}'
    # Fetch top users from Redis
    leaderboard_entries = await r.zrevrange(key, 0, limit-1, withscores=True)

    # Format the output
    result = [{"user_id":  int(entry[0]), "score": entry[1]}
              for entry in leaderboard_entries]

    return result


@router.get("/leaderboard/", response_model=list[schemas.LeaderboardOut])
async def get_leaderboard(
        request: Request,
        limit: int = Query(
            10, gt=0, le=100, description="The number of top users to fetch. Default is 10."),
        r: aioredis.Redis = Depends(get_redis_feed_db)):
    """
    Fetch the leaderboard.

    This endpoint returns the top N users based on their weekly scores.

    Parameters:
    - limit (int): The number of top users to fetch. Default is 10.
    - r (aioredis.Redis): The Redis instance, injected by FastAPI.

    Returns:
    - List[schemas.LeaderboardOut]: A list of leaderboard entries.
    """

    return await get_leaderboard_(limit, r)


@router.get("/{user_id}/", response_model=list[schemas.UserChallengeOut])
async def get_user_challenge(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(oauth2.get_current_user)
):
    if current_user.user_id != user_id:
        raise NotAuthorisedException()
    # Get the current date
    current_date = datetime.now()

    # Query the database to get the challenges created today for the given user_id
    query = db.query(models.User_Challenge).filter(
        models.User_Challenge.user_id == user_id,
        func.date(models.User_Challenge.created_at) == current_date.date()
    ).all()

    return query


@router.get("/all/{user_id}/", response_model=list[schemas.UserChallengeOut])
async def get_user_challenge(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(oauth2.get_current_user)
):
    if current_user.user_id != user_id:
        raise NotAuthorisedException()

    # Get the current date
    current_date = datetime.now()

    # Query the database to get the challenges created today for the given user_id
    query = db.query(models.User_Challenge).filter(
        models.User_Challenge.user_id == user_id
    ).all()

    return query


@router.get("/weekly_score/{user_id}/", response_model=list[schemas.ChallengeScoreOut])
async def calculate_weekly_score(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(oauth2.get_current_user)
):

    if current_user.user_id != user_id:
        raise NotAuthorisedException()
    # Get the current date
    current_date = datetime.now().date()

    # Calculate the date 7 days ago
    seven_days_ago = current_date - timedelta(days=7)

    # Query the database to get the sum of scores for challenges with progress equal to 1
    # created in the past 7 days for the given user_id, grouped by the date
    query = (
        db.query(
            func.date(
                func.timezone('Australia/Melbourne',
                              models.User_Challenge.created_at)
            ).label("date"),
            func.sum(
                case((models.User_Challenge.progress ==
                     1, models.Challenge.score), else_=0)
            ).label("score"),
            func.sum(
                case((models.User_Challenge.progress ==
                     1, models.Challenge.score), else_=0)

            ).filter(models.Challenge.type == 'distance_travelled').label("distance_travelled_score"),
            func.sum(
                case((models.User_Challenge.progress ==
                     1, models.Challenge.score), else_=0)

            ).filter(models.Challenge.type == 'route_generation').label("route_generation_score"),
            func.sum(
                case((models.User_Challenge.progress ==
                     1, models.Challenge.score), else_=0)

            ).filter(models.Challenge.type == 'favourite_sharing').label("favourite_sharing_score"),
        )
        .join(models.Challenge, models.User_Challenge.challenge_id == models.Challenge.id)
        .filter(
            models.User_Challenge.user_id == user_id,
            models.User_Challenge.progress == 1,
            func.date(models.User_Challenge.created_at) >= seven_days_ago,
        )
        .group_by(func.date(
            func.timezone('Australia/Melbourne',
                          models.User_Challenge.created_at)
        ).label("date"),)
    )

    # Execute the query and fetch the results
    result = query.all()

    return result


@async_retry()
async def update_score_in_redis(user_id: int, score: float, r: aioredis.Redis):
    # Get the current week number and year
    current_date = datetime.now()
    year, week_num = current_date.isocalendar()[0:2]

    # Add the user and their score to the ZSET for the current week
    key = f'challenge_leaderboard_score:{year}:{week_num}'
    await r.zincrby(key, score, user_id)


async def add_challenge_common(
        request: Request,
        user_id: int,
        challenge_data: schemas.DistanceTravelledChallenge,
        challenge_type: str,
        progress_calculator: Callable,
        db: Session,
        r: aioredis.Redis,
        current_user: schemas.User
):

    if current_user.user_id != user_id:
        raise NotAuthorisedException()

    challenges = db.query(models.Challenge).filter(
        models.Challenge.type == challenge_type).all()
    current_date = datetime.now()
    year = current_date.year
    month = current_date.month
    day = current_date.day

    for challenge in challenges:
        progress = progress_calculator(challenge_data, challenge)
        progress = min(progress, 1.0)  # Ensure progress does not exceed 1.0

        user_challenge = db.query(models.User_Challenge).filter(
            models.User_Challenge.user_id == user_id,
            models.User_Challenge.challenge_id == challenge.id,
            models.User_Challenge.year == year,
            models.User_Challenge.month == month,
            models.User_Challenge.day == day
        ).first()

        if user_challenge:
            user_challenge.progress = progress
            user_challenge.created_at = current_date
        else:
            user_challenge = models.User_Challenge(
                user_id=user_id,
                challenge_id=challenge.id,
                year=year,
                month=month,
                day=day,
                created_at=current_date,
                progress=progress
            )
            db.add(user_challenge)

        db.commit()
        db.refresh(user_challenge)

        # If the progress is 1, and score is not added yet, update the score in Redis
        if progress == 1.0 and not user_challenge.score_added:
            # Use the score from the challenge
            await update_score_in_redis(user_id, challenge.score, r)
            user_challenge.score_added = True
            db.commit()

    return {
        "details": {
            "type": "challenge_updated",
            "msg": "Challenge updated successfully"
        }
    }


def distance_travelled_calculator(challenge_data, challenge):
    return challenge_data.steps / (challenge.grade * 5000)


@router.post("/distance_travelled/{user_id}/", status_code=201)
async def add_challenge_distance_travelled(
        request: Request,
        user_id: int,
        challenge_data: schemas.DistanceTravelledChallenge,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    return await add_challenge_common(
        request,
        user_id,
        challenge_data,
        "distance_travelled",
        distance_travelled_calculator,
        db,
        r,
        current_user
    )


def route_generation_calculator(challenge_data: schemas.RouteGenerationChallenge, challenge):

    progress = 0

    if challenge.grade == 1:
        progress = min(challenge_data.routes_generated, 1)
    elif challenge.grade == 2:
        progress = min(challenge_data.routes_generated / 5, 1)
    elif challenge.grade == 3:
        progress = min(challenge_data.routes_generated / 10, 1)

    return progress


@router.post("/route_generation/{user_id}/", status_code=201)
async def add_challenge_route_generation(
        request: Request,
        user_id: int,
        challenge_data: schemas.RouteGenerationChallenge,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    return await add_challenge_common(
        request,
        user_id,
        challenge_data,
        "route_generation",
        route_generation_calculator,
        db,
        r,
        current_user
    )


def favourite_sharing_calculator(challenge_data: schemas.RouteFavChallenge, challenge):

    progress = 0

    if challenge.grade == 1:
        progress = min(challenge_data.routes_favourited_shared / 10, 1)
    elif challenge.grade == 2:
        progress = min(challenge_data.routes_favourited_shared / 20, 1)
    elif challenge.grade == 3:
        progress = min(challenge_data.routes_favourited_shared / 50, 1)

    return progress


@router.post("/favourite_sharing/{user_id}/", status_code=201)
async def add_challenge_favourite_sharing(
        request: Request,
        user_id: int,
        challenge_data: schemas.RouteFavChallenge,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):

    return await add_challenge_common(
        request,
        user_id,
        challenge_data,
        "favourite_sharing",
        favourite_sharing_calculator,
        db,
        r,
        current_user
    )
