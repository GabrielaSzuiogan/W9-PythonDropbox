from .core import router as core_router
from .auth import router as auth_router
from .config import settings

__all__ = ["core_router", "auth_router","settings"]