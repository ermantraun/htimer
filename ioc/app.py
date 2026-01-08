"""Composition root for the application IoC container."""
from dishka import Provider
from .common import DBProvider
from .users import UserProvider


def get_providers() -> list[Provider]:
    """
    Returns the list of all providers for the application.
    This is the single composition root for dependency injection.
    """
    return [
        DBProvider(),
        UserProvider(),
    ]
