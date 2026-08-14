"""SQLAlchemy Database Instance Module.

Defines the SQLAlchemy 2.0 DeclarativeBase and initializes the central Flask-SQLAlchemy extension.
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative Base class for all SQLAlchemy ORM database models."""

    pass


# Global SQLAlchemy database extension instance
db: SQLAlchemy = SQLAlchemy(model_class=Base)
