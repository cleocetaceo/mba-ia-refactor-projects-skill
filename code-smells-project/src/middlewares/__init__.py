from src.middlewares.auth import require_admin
from src.middlewares.error_handler import register_error_handlers

__all__ = ["register_error_handlers", "require_admin"]
