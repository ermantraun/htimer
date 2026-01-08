"""IoC (Inversion of Control) package for dependency injection."""
from .app import get_providers

# For backward compatibility with existing code
app = get_providers()

__all__ = ['get_providers', 'app']
