from fastapi import Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

from .config import settings

templates = Jinja2Templates(directory="app/templates")

security = HTTPBasic()

LOGS_CATEGORIES = ["Auth", "Search", "Route", "Track", "User", "Vote", "Other"]


def get_log_category(path: str) -> str:
    if path.startswith("/login"):
        return "Auth"
    elif path.startswith("/search"):
        return "Search"
    elif path.startswith("/route"):
        return "Route"
    elif path.startswith("/track"):
        return "Track"
    elif path.startswith("/user"):
        return "User"
    elif path.startswith("/vote"):
        return "Vote"
    else:
        return "Other"


def get_current_username_doc(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(
        credentials.username, settings.DOC_USERNAME)
    correct_password = secrets.compare_digest(
        credentials.password, settings.DOC_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
