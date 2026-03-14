from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class CreateUserIn(BaseModel):
    name: str = Field(
        examples=["John Doe"], description="The name of the user", max_length=150
    )
    email: str = Field(
        examples=["john.doe@example.com"],
        description="The email of the user",
        max_length=150,
    )
    password: str = Field(
        examples=["strong_password"],
        description="The password of the user",
        min_length=8,
    )
    role: UserRole = Field(examples=[UserRole.USER], description="The role of the user")


class CreateUserOut(BaseModel):
    user_uuid: UUID = Field(
        examples=["123e4567-e89b-12d3-a456-426614174000"],
        description="The UUID of the created user",
    )
