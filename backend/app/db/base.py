# Import base class
from .base_class import Base

# Import all models here for Alembic
from ..models.user import User  # noqa
from ..models.audit import AuditLog  # noqa
from ..models.content import Content  # noqa
from ..models.template import Template  # noqa
from ..models.generation import Generation  # noqa

# Make sure all models are imported before initializing the database
__all__ = ["Base"] 