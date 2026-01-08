"""Composition root for the application IoC container.

Важные правила:
- Единственная точка сборки прод-контейнера находится здесь.
- Порядок providers стабилен и предсказуем.
- В тестах поверх этого набора добавляется test-provider с override'ами.
"""

from __future__ import annotations

from dishka import AsyncContainer, Provider, make_async_container

from .common import DBProvider
from .user import UserProvider


def get_providers() -> list[Provider]:
    """Список production providers в стабильном порядке."""
    return [DBProvider(), UserProvider()]


def build_container(*extra_providers: Provider) -> AsyncContainer:
    """Собрать AsyncContainer.

    extra_providers предназначены для тестов/обвязки и добавляются *перед*
    production providers, чтобы их регистрации могли предсказуемо переопределять
    дефолтные.
    """

    return make_async_container(*extra_providers, *get_providers())
