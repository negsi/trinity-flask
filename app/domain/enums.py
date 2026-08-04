from enum import Enum


class ActorType(str, Enum):
    """
    Enumeration representing the type of entity performing an action or sending a message within the system.

    Inheriting from `str` and `Enum` ensures that members serialize directly 
    to plain strings during JSON parsing and database persistence.

    Attributes:
        USER (str): Represents a human user interacting via the interface.
        AGENT (str): Represents an autonomous AI agent operating within the application context.
        SYSTEM (str): Represents automated system processes or background event triggers.
    """
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"