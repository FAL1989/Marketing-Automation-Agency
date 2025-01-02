"""
Package de modelos da aplicação.
"""

# Importa os modelos para que o Alembic possa detectá-los
from .user import User  # noqa
from .audit import AuditLog  # noqa
from .content import Content  # noqa
from .template import Template  # noqa
from .generation import Generation  # noqa

__all__ = [
    "User",
    "AuditLog",
    "Content",
    "Template",
    "Generation"
]
