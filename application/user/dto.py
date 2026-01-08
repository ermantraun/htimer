"""
Backward compatibility re-export.
User DTOs have been moved to modules/users/application/dto.py
"""
from modules.users.application.dto import (
    CreateUserInDTO,
    CreateUserOutDTO,
    UpdateUserInDTO,
    UpdateUserOutDTO,
    GetUsersInDto,
    GetUserIn,
    GetUsersOutDTO,
)

__all__ = [
    'CreateUserInDTO',
    'CreateUserOutDTO',
    'UpdateUserInDTO',
    'UpdateUserOutDTO',
    'GetUsersInDto',
    'GetUserIn',
    'GetUsersOutDTO',
]