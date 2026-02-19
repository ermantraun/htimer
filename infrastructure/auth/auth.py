from application import common_interfaces
from application.common_exceptions import InvalidToken
from application.user import interfaces
from . import interfaces as auth_interfaces
from config import Config
from datetime import timedelta
from typing import Any
from uuid import UUID
import jwt


class Auth(common_interfaces.Context, interfaces.TokenGenerator):
    def __init__(self, config: Config, clock: auth_interfaces.Clock ) -> None:
        self.context: dict[str, Any] = {}
        self.config = config.jwt
        self.clock = clock

    async def generate(self, user_uuid: UUID) -> str:
        payload: dict[str, Any] = {
                    "iss": "app",
                    "sub": str(user_uuid),
                    "iat": await self.clock.now(),
                    "exp": await self.clock.now() + timedelta(hours=self.config.expiration_days)
                }
        
        token = jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm) # type: ignore
        
        return token


    def get_current_user_uuid(self) -> UUID | InvalidToken:
        if hasattr(self.context, "get_current_user_uuid") and callable(getattr(self.context, "get_current_user_uuid")):
            value = getattr(self.context, "get_current_user_uuid")()
            if isinstance(value, UUID):
                return value
            if isinstance(value, InvalidToken):
                return value

        value: object | None = None
        if hasattr(self.context, "get") and callable(getattr(self.context, "get")):
            getter = getattr(self.context, "get")
            value = getter("current_user_uuid") or getter("user_uuid")
        elif hasattr(self.context, "current_user_uuid"):
            value = getattr(self.context, "current_user_uuid")
        elif hasattr(self.context, "user_uuid"):
            value = getattr(self.context, "user_uuid")

        if isinstance(value, UUID):
            return value

        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError:
                return InvalidToken("Invalid user uuid in context")

        return InvalidToken("User uuid not found in context")