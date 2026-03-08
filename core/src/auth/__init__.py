"""Authentication module for Convoy API."""

from .key_generator import generate_api_key, hash_api_key, validate_key_format
from .dependencies import AuthenticatedProject, get_current_project, get_optional_project
from .admin import require_admin

__all__ = [
    # Key generation
    "generate_api_key",
    "hash_api_key",
    "validate_key_format",
    # Dependencies
    "AuthenticatedProject",
    "get_current_project",
    "get_optional_project",
    # Admin
    "require_admin",
]
