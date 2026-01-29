"""
Base SQLAlchemy e configuração comum.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base para todos os modelos ORM."""

    pass
