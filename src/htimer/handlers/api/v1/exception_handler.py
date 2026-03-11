"""from fastapi import Request, status, exceptions
from fastapi.responses import JSONResponse
import json
import jwt
from application.exceptions import UnAuthorizedError, ValidationError as AppValidationError
from infrastructure.db.exceptions import RecordDontExistsError
from sqlalchemy.exc import IntegrityError
from infrastructure.file_storage.exceptions import NotFoundFileError, AlreadyExistsFileError

# Этот хендлер срабатывает, когда возникает ошибка валидации данных.
async def validation_exception_handler(request: Request, exc: AppValidationError | exceptions.RequestValidationError) -> JSONResponse:
    problem_fields = {error["loc"][-1]: error["msg"] for error in exc.errors()}
    
    error_message = {
        "message": "Conflict field/fields",
        "problem_fields": problem_fields
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_message
    )

# Этот хендлер срабатывает, когда возникает ошибка уникальности данных в базе данных.
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    detail = str(exc.orig)
    problem_fields = {}

    if "uq_user_login" in detail:
        problem_fields["login"] = "already exists"
    elif "uq_user_email" in detail:
        problem_fields["email"] = "already exists"
    elif "uq_video_name_author" in detail:
        problem_fields["name"] = "already exists for this author"
    elif "uq_heat_map_video" in detail:
        problem_fields["video"] = "already has a heat map"
    else:
        raise exc

    error_message = {
        "message": "Conflict field/fields",
        "problem_fields": problem_fields
    }
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=error_message
    )

# Этот хендлер срабатывает, когда токен истек.
async def expired_token_handler(request: Request, exc: jwt.ExpiredSignatureError):
    return JSONResponse(
        status_code=401,
        content={"message": "Token has expired"},
    )

# Этот хендлер срабатывает, когда токен недействителен.
async def invalid_token_handler(request: Request, exc: jwt.InvalidTokenError):
    return JSONResponse(
        status_code=401,
        content={"message": "Invalid token"},
    )

# Этот хендлер срабатывает, когда токен отсутствует или имеет неправильный формат.
async def unauthorized_handler(request: Request, exc: UnAuthorizedError):
    return JSONResponse(
        status_code=401,
        content={"message": "Authorization token is missing or improperly formatted"},
    )

# Этот хендлер срабатывает, когда возникает ошибка значения.
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": str(exc)},
    )

# Этот хендлер срабатывает, когда запись не найдена в базе данных.
async def record_not_found_handler(request: Request, exc: RecordDontExistsError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": str(exc)},
    )

async def file_not_found_handler(request: Request, exc: NotFoundFileError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": str(exc)},
    )

async def file_already_exists_handler(request: Request, exc: AlreadyExistsFileError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"message": str(exc)},
    )

async def default_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error"},
    )

all_handlers = { 
    IntegrityError: integrity_error_handler,
    jwt.ExpiredSignatureError: expired_token_handler,
    jwt.InvalidTokenError: invalid_token_handler,
    UnAuthorizedError: unauthorized_handler,
    AppValidationError: validation_exception_handler,
    exceptions.RequestValidationError: validation_exception_handler,
    ValueError: value_error_handler,
    RecordDontExistsError: record_not_found_handler,
    NotFoundFileError: file_not_found_handler,
    AlreadyExistsFileError: file_already_exists_handler,
    Exception: default_exception_handler,
}"""


from fastapi import Request, status
from fastapi.responses import JSONResponse
from htimer.application.common_exceptions import AuthorizationError

#Authorization errors
async def authorization_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"message": str(exc)},
    )

#infrastructure exceptions
async def invalid_token_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": str(exc)},
    )

