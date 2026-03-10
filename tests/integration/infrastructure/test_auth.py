from uuid import uuid4
from typing import Any, cast

import jwt

from htimer.application import common_interfaces
from htimer.application.user import interfaces as user_interfaces
from htimer.application.common_exceptions import InvalidTokenError
from htimer.config import Config


async def test_generate_token_success(
    infra_auth_token_generator: user_interfaces.TokenGenerator,
    test_config: Config,
):
    user_uuid = uuid4()

    token = await infra_auth_token_generator.generate(user_uuid)

    decoded = jwt.decode(token, test_config.jwt.secret_key, algorithms=[test_config.jwt.algorithm]) # type: ignore
    assert decoded["sub"] == str(user_uuid)


def test_get_current_user_uuid_from_context_dict(
    infra_auth_context: common_interfaces.Context,
):
    user_uuid = uuid4()
    auth_context = cast(Any, infra_auth_context)
    auth_context.context = {"current_user_uuid": str(user_uuid)}

    result = infra_auth_context.get_current_user_uuid()

    assert result == user_uuid


def test_get_current_user_uuid_invalid_context(
    infra_auth_context: common_interfaces.Context,
):
    auth_context = cast(Any, infra_auth_context)
    auth_context.context = {}

    result = infra_auth_context.get_current_user_uuid()

    assert isinstance(result, InvalidTokenError)
