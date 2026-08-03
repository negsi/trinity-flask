"""
Type Definition Module.

Defines protocol interfaces and typing utilities for custom Flask app extensions.
"""

from flask import current_app
from typing import Protocol, Callable, Any, cast


class DebuggableFlask(Protocol):
    """Protocol defining extended Flask instances containing a debug printing method `d`."""
    d: Callable[..., Any]


def debug_app() -> DebuggableFlask:
    """Helper function to cast the active current_app instance to DebuggableFlask."""
    return cast(DebuggableFlask, current_app)
