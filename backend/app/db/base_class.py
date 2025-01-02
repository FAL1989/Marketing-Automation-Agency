"""
Classe base para modelos SQLAlchemy
"""

from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr

@as_declarative()
class Base:
    """
    Classe base para todos os modelos SQLAlchemy.
    Fornece um nome de tabela automático baseado no nome da classe.
    """
    id: Any
    __name__: str
    
    # Gera o nome da tabela automaticamente
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Gera o nome da tabela a partir do nome da classe em snake_case.
        Por exemplo: UserProfile -> user_profile
        """
        return cls.__name__.lower()

    def dict(self) -> dict:
        """Converte o modelo para dicionário"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

__all__ = ["Base"] 