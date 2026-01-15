"""Shared API - Common API utilities and middleware."""

from .exception_handlers import (
    DOMAIN_EXCEPTION_MAP,
    SECURITY_EXCEPTION_MAP,
    domain_exception_handler,
    security_exception_handler,
)
from .schemas import EntitySchema

__all__ = [
    "DOMAIN_EXCEPTION_MAP",
    "SECURITY_EXCEPTION_MAP",
    "domain_exception_handler",
    "security_exception_handler",
    "EntitySchema",
]
