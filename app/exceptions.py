from fastapi import HTTPException


class CustomHTTPException(HTTPException):
    default_type = "default_type"
    default_msg = "DefaultMessage"
    default_status_code = 400

    def __init__(self):
        super().__init__(
            status_code=self.default_status_code,
            detail={
                "type": self.default_type,
                "msg": self.default_msg
            })


class InvalidCredentialsException(CustomHTTPException):
    default_status_code = 401
    default_type = "invalid_credentials"
    default_msg = "Invalid credentials"

    def __init__(self):
        super().__init__()
        self.headers = {"WWW-Authenticate": "Bearer"}


class UserNotFoundException(CustomHTTPException):
    default_status_code = 404
    default_type = "user_not_found"
    default_msg = "User not found"


class UserAlreadyExistsException(CustomHTTPException):
    default_status_code = 400
    default_type = "user_already_exists"
    default_msg = "User already exists"


class InvalidRefreshTokenException(CustomHTTPException):
    default_status_code = 404
    default_type = "invalid_refresh_token"
    default_msg = "Invalid refresh token"


class NotAuthorisedException(CustomHTTPException):
    default_status_code = 403
    default_type = "not_authorised"
    default_msg = "Not authorised"


class LocationNotFoundException(CustomHTTPException):
    default_status_code = 404
    default_type = "no_location"
    default_msg = "Not found any location in the given area"


class InvalidSearchQueryException(CustomHTTPException):
    default_status_code = 400
    default_type = "invalid_search_query"
    default_msg = "Invalid search query"


class RouteNotFoundException(CustomHTTPException):
    default_status_code = 404
    default_type = "no_route"
    default_msg = "Not found any route in the given area"


class ParametersTooLargeException(CustomHTTPException):
    default_status_code = 400
    default_type = "parameters_too_large"
    default_msg = "Parameters too large"


class AlreadyVotedException(CustomHTTPException):
    default_status_code = 409
    default_type = "already_voted"
    default_msg = "Already voted"


class VoteNotFoundException(CustomHTTPException):
    default_status_code = 404
    default_type = "vote_not_found"
    default_msg = "Vote not found"


class ImageNotFoundException(CustomHTTPException):
    default_status_code = 404
    default_type = "image_not_found"
    default_msg = "Image not found"
