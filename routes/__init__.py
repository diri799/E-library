"""Application routes package."""

from routes.admin import admin_bp
from routes.auth import auth_bp, role_required
from routes.user import user_bp

__all__ = ["auth_bp", "admin_bp", "user_bp", "role_required"]
