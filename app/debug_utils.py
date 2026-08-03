"""
Debug Proxy Utilities.

Provides a shorthand proxy helper to invoke debug printing on the active Flask context.
"""

from flask import current_app
from typing import cast
from .types import DebuggableFlask


def d(*args, **kwargs):
    """
    Global shortcut function to execute `app.d(...)` debug helper on `current_app`.
    """
    if hasattr(current_app, "d"):
        cast(DebuggableFlask, current_app).d(*args, **kwargs)
