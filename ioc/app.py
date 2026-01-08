
from __future__ import annotations

from dishka import AsyncContainer, Provider, make_async_container

from .common import DBProvider
from .user import UserProvider


def get_providers() -> list[Provider]:
    return [DBProvider(), UserProvider()]


def build_container(*extra_providers: Provider) -> AsyncContainer:
    return make_async_container(*extra_providers, *get_providers())
