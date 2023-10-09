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
        r: aioredis.Redis,
        db: Session
):
    current_date_melbourne = db.query(
        func.date(func.timezone('Australia/Melbourne', func.now()))
    ).scalar()

    year = current_date_melbourne.year
    week_num = current_date_melbourne.strftime("%U")  # gets week number

    # Fetch top users from Redis for the current week
    key = f'challenge_leaderboard_score:{year}:{week_num}'
    # Fetch top users from Redis
    leaderboard_entries = await r.zrevrange(key, 0, limit-1, withscores=True)

    # Format the output
    result = [{"username":  entry[0], "score": entry[1]}
              for entry in leaderboard_entries]

    return result


@router.get("/leaderboard/", response_model=list[schemas.LeaderboardOut])
async def get_leaderboard(
        request: Request,
        limit: int = Query(
            10, gt=0, le=100,
            description="The number of top users to fetch. Default is 10."
        ),
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db)
):
    """
    Fetch the leaderboard.

    This endpoint returns the top N users based on their weekly scores.

    Parameters:
    - limit (int): The number of top users to fetch. Default is 10.
    - r (aioredis.Redis): The Redis instance, injected by FastAPI.

    Returns:
    - List[schemas.LeaderboardOut]: A list of leaderboard entries.
    """

    return await get_leaderboard_(limit, r, db)


@router.get("/{user_id}/", response_model=list[schemas.UserChallengeOut])
async def get_user_challenge(
        request: Request,
        user_id: int,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    """
    Fetch the user's challenges created today.

    This endpoint returns the challenges created today for a specified user.

    Parameters:
    - user_id (int): The ID of the user to fetch challenges for.
    - db (Session): The database session, injected by FastAPI.
    - current_user (schemas.User): The current authenticated user,
      injected by FastAPI.

    Returns:
    - List[schemas.UserChallengeOut]: A list of user challenges created today.
    """

    if current_user.user_id != user_id:
        raise NotAuthorisedException()
    # Get the current date
    current_date_melbourne = db.query(
        func.date(func.timezone('Australia/Melbourne', func.now()))
    ).scalar()

    # Query the database to get the challenges created today
    # for the given user_id
    query = db.query(models.User_Challenge).filter(
        models.User_Challenge.user_id == user_id,
        func.date(models.User_Challenge.created_at) == current_date_melbourne
    ).all()

    return query


@router.get("/all/{user_id}/", response_model=list[schemas.UserChallengeOut])
async def get_all_user_challenge(
        request: Request,
        user_id: int,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    """
    Fetch all challenges for a specified user.

    This endpoint returns all the challenges for a specified user.

    Parameters:
    - user_id (int): The ID of the user to fetch challenges for.
    - db (Session): The database session, injected by FastAPI.
    - current_user (schemas.User): The current authenticated user,
      injected by FastAPI.

    Returns:
    - List[schemas.UserChallengeOut]: A list of all user challenges.
    """

    if current_user.user_id != user_id:
        raise NotAuthorisedException()

    # Query the database to get the challenges created today
    # for the given user_id
    query = db.query(models.User_Challenge).filter(
        models.User_Challenge.user_id == user_id
    ).all()

    return query


@router.get("/weekly_score/{user_id}/",
            response_model=list[schemas.ChallengeScoreOut])
async def calculate_weekly_score(
        request: Request,
        user_id: int,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    """
    Calculate and fetch the weekly score for a specified user.

    This endpoint calculates and returns the sum of scores for challenges
    with progress equal to 1,
    created in the past 7 days for a specified user, grouped by the date.

    Parameters:
    - user_id (int): The ID of the user to calculate the weekly score for.
    - db (Session): The database session, injected by FastAPI.
    - current_user (schemas.User): The current authenticated user,
      injected by FastAPI.

    Returns:
    - List[schemas.ChallengeScoreOut]: A list of challenge scores.
    """

    if current_user.user_id != user_id:
        raise NotAuthorisedException()
    # Get the current date in Melbourne timezone
    current_date_melbourne = db.query(
        func.date(func.timezone('Australia/Melbourne', func.now()))
    ).scalar()

    # Calculate the date 7 days ago based on Melbourne time
    seven_days_ago = current_date_melbourne - timedelta(days=7)

    # Query the database to get the sum of scores for challenges
    # with progress equal to 1
    # created in the past 7 days for the given user_id, grouped by the date
    query = (
        db.query(
            func.date(
                models.User_Challenge.created_at)
            .label("date"),
            func.sum(
                case((models.User_Challenge.progress ==
                     1, models.Challenge.score), else_=0)
            ).label("score"),

            func.sum(
                case((models.User_Challenge.progress ==
                     1, models.Challenge.score), else_=0)

            ).filter(models.Challenge.type == 'route_generation')
            .label("route_generation_score"),
            func.sum(
                case((models.User_Challenge.progress ==
                     1, models.Challenge.score), else_=0)

            ).filter(models.Challenge.type == 'favourited')
            .label("favourited_score"),
            func.sum(
                case((models.User_Challenge.progress ==
                     1, models.Challenge.score), else_=0)

            ).filter(models.Challenge.type == 'shared')
            .label("shared_score"),
            func.sum(
                case((models.User_Challenge.progress ==
                     1, models.Challenge.score), else_=0)

            ).filter(models.Challenge.type == 'published')
            .label("published_score"),
            func.sum(
                case((models.User_Challenge.progress ==
                     1, models.Challenge.score), else_=0)

            ).filter(models.Challenge.type == 'read_tips')
            .label("read_tips_score"),
            func.sum(
                case((models.User_Challenge.progress ==
                     1, models.Challenge.score), else_=0)

            ).filter(models.Challenge.type == 'logged_in')
            .label("logged_in_score"),
            func.sum(
                case((models.User_Challenge.progress ==
                     1, models.Challenge.score), else_=0)

            ).filter(models.Challenge.type == 'accessed_global_feed')
            .label("accessed_global_feed_score"),



        )
        .join(
            models.Challenge,
            models.User_Challenge.challenge_id == models.Challenge.id
        )
        .filter(
            models.User_Challenge.user_id == user_id,
            models.User_Challenge.progress == 1,
            func.date(models.User_Challenge.created_at) >= seven_days_ago,
        )
        .group_by(func.date(
            models.User_Challenge.created_at
        )
            .label("date"),)
    )

    # Execute the query and fetch the results
    result = query.all()

    return result


@async_retry()
async def update_score_in_redis(
        user_id: int,
        score: float,
        r: aioredis.Redis,
        db: Session
):
    """
    Update user's score in Redis.

    This asynchronous function updates the score of a specific user in Redis.

    Parameters:
    - user_id (int): The ID of the user whose score needs to be updated.
    - score (float): The score to be updated in Redis.
    - r (aioredis.Redis): The Redis instance.
    - db (Session): The database session.

    Raises:
    - Any exceptions raised by the Redis operations
      will be handled by the async_retry decorator.
    """

    # Get the current year and week number from the database
    current_date_melbourne = db.query(
        func.date(func.timezone('Australia/Melbourne', func.now()))
    ).scalar()

    year = current_date_melbourne.year
    week_num = current_date_melbourne.strftime("%U")  # gets week number

    # Add the user and their score to the ZSET for the current week
    key = f'challenge_leaderboard_score:{year}:{week_num}'
    username = db.query(models.User.username).filter(
        models.User.user_id == user_id).first()[0]
    print(username)

    await r.zincrby(key, score, username)

    # Check if the key already has an expiration time set
    ttl = await r.ttl(key)

    if ttl == -1:  # -1 indicates that the key does not have an expiration time
        # Set the expiration time to 4 weeks (in seconds)
        await r.expire(key, 4 * 7 * 24 * 60 * 60)


async def add_challenge_common(
        request: Request,
        user_id: int,
        challenge_data: schemas.BaseModel,
        challenge_type: str,
        progress_calculator: Callable,
        db: Session,
        r: aioredis.Redis,
        current_user: schemas.User
):
    """
    Common function to add a challenge.

    This function is used to add a challenge for a user,
    and updates the progress of the challenge.

    Parameters:
    - request (Request): The request object.
    - user_id (int): The ID of the user to add the challenge for.
    - challenge_data (schemas.DistanceTravelledChallenge): The challenge data.
    - challenge_type (str): The type of the challenge.
    - progress_calculator (Callable): The function to calculate the progress.
    - db (Session): The database session.
    - r (aioredis.Redis): The Redis instance.
    - current_user (schemas.User): The current authenticated user.

    Returns:
    - dict: A dictionary containing details about the update status.
    """

    if current_user.user_id != user_id:
        raise NotAuthorisedException()

    challenges = db.query(models.Challenge).filter(
        models.Challenge.type == challenge_type).all()
    # Get the current date in Melbourne time from the database
    current_datetime_melbourne = db.query(
        func.timezone('Australia/Melbourne', func.now())
    ).scalar()

    year = current_datetime_melbourne.year
    month = current_datetime_melbourne.month
    day = current_datetime_melbourne.day

    for challenge in challenges:
        progress = progress_calculator(challenge_data, challenge)

        user_challenge = db.query(models.User_Challenge).filter(
            models.User_Challenge.user_id == user_id,
            models.User_Challenge.challenge_id == challenge.id,
            models.User_Challenge.year == year,
            models.User_Challenge.month == month,
            models.User_Challenge.day == day
        ).first()

        if user_challenge:
            user_challenge.progress += progress
            user_challenge.progress = min(user_challenge.progress, 1.0)
            user_challenge.created_at = current_datetime_melbourne
        else:
            user_challenge = models.User_Challenge(
                user_id=user_id,
                challenge_id=challenge.id,
                year=year,
                month=month,
                day=day,
                created_at=current_datetime_melbourne,
                progress=min(progress, 1.0)
            )
            db.add(user_challenge)

        db.commit()
        db.refresh(user_challenge)

        # If the progress is 1, and score is not added, update score in Redis
        if progress == 1.0 and not user_challenge.score_added:
            # Use the score from the challenge
            await update_score_in_redis(user_id, challenge.score, r, db)
            user_challenge.score_added = True
            db.commit()

    return {
        "details": {
            "type": "challenge_updated",
            "msg": "Challenge updated successfully"
        }
    }


def route_generation_calculator(
        challenge_data: schemas.RouteGenerationChallenge,
        challenge
):
    """
    Calculate the progress for route generation challenge.

    This function calculates the progress
    for the route generation challenge
    based on the routes generated and grade.

    Parameters:
    - challenge_data (schemas.RouteGenerationChallenge):
      The challenge data containing the routes generated.
    - challenge: The challenge object.

    Returns:
    - float: The calculated progress.
    """

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
    """
    Add route generation challenge by incrementing the existing progress..

    This endpoint is used to add a route generation challenge
    for a specific user.

    Parameters:
    - request (Request): The request object.
    - user_id (int): The ID of the user to add the challenge for.
    - challenge_data (schemas.RouteGenerationChallenge): The challenge data.
    - db (Session): The database session, injected by FastAPI.
    - r (aioredis.Redis): The Redis instance, injected by FastAPI.
    - current_user (schemas.User): The current authenticated user,
      injected by FastAPI.

    Returns:
    - The response message.
    """

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


def favourite_calculator(
        challenge_data: schemas.RouteFavChallenge,
        challenge
):
    """
    Calculate the progress for favourite challenge.

    This function calculates the progress
    for the favourite sharing challenge
    based on the routes favourited/shared and grade.

    Parameters:
    - challenge_data (schemas.RouteFavChallenge):
      The challenge data containing the routes favourited/shared.
    - challenge: The challenge object.

    Returns:
    - float: The calculated progress.
    """

    progress = 0

    if challenge.grade == 1:
        progress = min(challenge_data.routes_favourited, 1)
    elif challenge.grade == 2:
        progress = min(challenge_data.routes_favourited / 5, 1)
    elif challenge.grade == 3:
        progress = min(challenge_data.routes_favourited / 10, 1)

    return progress


@router.post("/favourited/{user_id}/", status_code=201)
async def add_challenge_favourite(
        request: Request,
        user_id: int,
        challenge_data: schemas.RouteFavChallenge,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    """
    Add favouriting challenge by incrementing the existing progress.

    This endpoint is used to add a favourite sharing challenge
    for a specific user.

    Parameters:
    - request (Request): The request object.
    - user_id (int): The ID of the user to add the challenge for.
    - challenge_data (schemas.RouteFavChallenge): The challenge data.
    - db (Session): The database session, injected by FastAPI.
    - r (aioredis.Redis): The Redis instance, injected by FastAPI.
    - current_user (schemas.User): The current authenticated user,
      injected by FastAPI.

    Returns:
    - The response message.
    """

    return await add_challenge_common(
        request,
        user_id,
        challenge_data,
        "favourited",
        favourite_calculator,
        db,
        r,
        current_user
    )


def shared_calculator(
        challenge_data: schemas.RouteShareChallenge,
        challenge
):
    """
    Calculate the progress for sharing challenge.

    This function calculates the progress
    for sharing route challenge
    based on the routes shared and grade.

    Parameters:
    - challenge_data (schemas.RouteShareChallenge):
      The challenge data containing the routes shared.
    - challenge: The challenge object.

    Returns:
    - float: The calculated progress.
    """

    progress = 0

    if challenge.grade == 1:
        progress = min(challenge_data.routes_shared, 1)
    elif challenge.grade == 2:
        progress = min(challenge_data.routes_shared / 5, 1)
    elif challenge.grade == 3:
        progress = min(challenge_data.routes_shared / 10, 1)

    return progress


@router.post("/shared/{user_id}/", status_code=201)
async def add_challenge_share(
        request: Request,
        user_id: int,
        challenge_data: schemas.RouteShareChallenge,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    """
    Add favourite sharing challenge by incrementing the existing progress.

    This endpoint is used to add a sharing challenge
    for a specific user.

    Parameters:
    - request (Request): The request object.
    - user_id (int): The ID of the user to add the challenge for.
    - challenge_data (schemas.RouteShareChallenge): The challenge data.
    - db (Session): The database session, injected by FastAPI.
    - r (aioredis.Redis): The Redis instance, injected by FastAPI.
    - current_user (schemas.User): The current authenticated user,
      injected by FastAPI.

    Returns:
    - The response message.
    """

    return await add_challenge_common(
        request,
        user_id,
        challenge_data,
        "shared",
        shared_calculator,
        db,
        r,
        current_user
    )


def publised_calculator(
        challenge_data: schemas.RoutePublishChallenge,
        challenge
):
    """
    Calculate the progress for publishing challenge
    by incrementing the existing progress.

    This function calculates the progress
    for the publish challenge
    based on the routes published and grade.

    Parameters:
    - challenge_data (schemas.RoutePublishChallenge):
      The challenge data containing the routes published.
    - challenge: The challenge object.

    Returns:
    - float: The calculated progress.
    """

    progress = 0

    if challenge.grade == 1:
        progress = min(challenge_data.routes_published, 1)
    elif challenge.grade == 2:
        progress = min(challenge_data.routes_published / 5, 1)
    elif challenge.grade == 3:
        progress = min(challenge_data.routes_published / 10, 1)

    return progress


@router.post("/published/{user_id}/", status_code=201)
async def add_challenge_publish(
        request: Request,
        user_id: int,
        challenge_data: schemas.RoutePublishChallenge,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    """
    Add favourite publishing challenge by incrementing the existing progress.

    This endpoint is used to add a published challenge
    for a specific user.

    Parameters:
    - request (Request): The request object.
    - user_id (int): The ID of the user to add the challenge for.
    - challenge_data (schemas.RoutePublishChallenge): The challenge data.
    - db (Session): The database session, injected by FastAPI.
    - r (aioredis.Redis): The Redis instance, injected by FastAPI.
    - current_user (schemas.User): The current authenticated user,
      injected by FastAPI.

    Returns:
    - The response message.
    """

    return await add_challenge_common(
        request,
        user_id,
        challenge_data,
        "published",
        publised_calculator,
        db,
        r,
        current_user
    )


def read_tips_calculator(
        challenge_data: schemas.ReadTipChallenge,
        challenge
):
    """
    Calculate the progress for reading tips challenge.

    This function calculates the progress
    for the read tips challenge
    based on the and grade.

    Parameters:
    - challenge_data (schemas.ReadTipChallenge):
      The challenge data containing the number of tips read.
    - challenge: The challenge object.

    Returns:
    - float: The calculated progress.
    """

    progress = 0

    if challenge.grade == 1:
        progress = min(challenge_data.tips_read, 1)
    elif challenge.grade == 2:
        progress = min(challenge_data.tips_read / 5, 1)
    elif challenge.grade == 3:
        progress = min(challenge_data.tips_read / 10, 1)

    return progress


@router.post("/tips_read/{user_id}/", status_code=201)
async def add_challenge_tips(
        request: Request,
        user_id: int,
        challenge_data: schemas.ReadTipChallenge,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    """
    Add tips read challenge by incrementing the existing progress.

    This endpoint is used to add a favourite sharing challenge
    for a specific user.

    Parameters:
    - request (Request): The request object.
    - user_id (int): The ID of the user to add the challenge for.
    - challenge_data (schemas.ReadTipChallenge): The challenge data.
    - db (Session): The database session, injected by FastAPI.
    - r (aioredis.Redis): The Redis instance, injected by FastAPI.
    - current_user (schemas.User): The current authenticated user,
      injected by FastAPI.

    Returns:
    - The response message.
    """

    return await add_challenge_common(
        request,
        user_id,
        challenge_data,
        "read_tips",
        shared_calculator,
        db,
        r,
        current_user
    )


def logged_in_cal(
        challenge_data: schemas.DailyLoggedInChallenge,
        challenge
):

    if challenge_data.logged_in:
        return 1
    else:
        return 0


@router.post("/logged_in/{user_id}/", status_code=201)
async def add_challenge_loggedin(
        request: Request,
        user_id: int,
        challenge_data: schemas.DailyLoggedInChallenge,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    """
    Add logged in challenge only one time a day.

    This endpoint is used to add a login challenge
    for a specific user.

    Parameters:
    - request (Request): The request object.
    - user_id (int): The ID of the user to add the challenge for.
    - challenge_data (schemas.DailyLoggedInChallenge): The challenge data.
    - db (Session): The database session, injected by FastAPI.
    - r (aioredis.Redis): The Redis instance, injected by FastAPI.
    - current_user (schemas.User): The current authenticated user,
      injected by FastAPI.

    Returns:
    - The response message.
    """

    return await add_challenge_common(
        request,
        user_id,
        challenge_data,
        "logged_in",
        logged_in_cal,
        db,
        r,
        current_user
    )


def accessed_feed_cal(
        challenge_data: schemas.AccessedGlobalFeedChallenge,
        challenge
):

    if challenge_data.accessed_global_feed:
        return 1
    else:
        return 0


@router.post("/accessed_global_feed/{user_id}/", status_code=201)
async def add_challenge_accessed_feed(
        request: Request,
        user_id: int,
        challenge_data: schemas.AccessedGlobalFeedChallenge,
        db: Session = Depends(get_db),
        r: aioredis.Redis = Depends(get_redis_feed_db),
        current_user: schemas.User = Depends(oauth2.get_current_user)
):
    """
    Add accessed global feed challenge only one time a day.

    This endpoint is used to add an accessed global feed challenge
    for a specific user.

    Parameters:
    - request (Request): The request object.
    - user_id (int): The ID of the user to add the challenge for.
    - challenge_data (schemas.AccessedGlobalFeedChallenge): The challenge data.
    - db (Session): The database session, injected by FastAPI.
    - r (aioredis.Redis): The Redis instance, injected by FastAPI.
    - current_user (schemas.User): The current authenticated user,
      injected by FastAPI.

    Returns:
    - The response message.
    """

    return await add_challenge_common(
        request,
        user_id,
        challenge_data,
        "accessed_global_feed",
        accessed_feed_cal,
        db,
        r,
        current_user
    )
