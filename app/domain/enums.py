"""
Domain Enumerations Module.

Centralized enumeration types used across domain models, database abstractions, and API interfaces.
"""

from enum import Enum


class ActorType(str, Enum):
    """
    Enumeration representing the type of entity performing an action or sending a message.

    Inheriting from `str` and `Enum` ensures direct string serialization during JSON formatting
    and database ORM persistence.
    """

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
