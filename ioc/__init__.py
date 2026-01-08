"""IoC (Inversion of Control) package.

Единый composition root: `ioc.app`.
Не экспортируем готовый список providers как переменную `app`, чтобы не было
зависимости от побочных эффектов импорта и случайного порядка сборки.
"""

from .app import build_container, get_providers

__all__ = ["build_container", "get_providers"]
