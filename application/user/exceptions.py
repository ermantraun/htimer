"""
Backward compatibility re-export.
User exceptions have been moved to modules/users/application/exceptions.py
"""
from modules.users.application.exceptions import (
    UserValidationError,
    InvalidNameError,
    InvalidEmailError,
    InvalidPasswordError,
    UserRepositoryError,
    EmailAlreadyExistsError,
    UserNotFoundError,
    InvalidToken,
    InvalidPasswordHashError,
    AdminIsNotProjectOwner,
    UserIsNotAdmin,
    UserCannotCreateUsersError,
    CannotChangeAdminSelfError,
    CannotChangeStatusSelfError,
)

__all__ = [
    'UserValidationError',
    'InvalidNameError',
    'InvalidEmailError',
    'InvalidPasswordError',
    'UserRepositoryError',
    'EmailAlreadyExistsError',
    'UserNotFoundError',
    'InvalidToken',
    'InvalidPasswordHashError',
    'AdminIsNotProjectOwner',
    'UserIsNotAdmin',
    'UserCannotCreateUsersError',
    'CannotChangeAdminSelfError',
    'CannotChangeStatusSelfError',
]