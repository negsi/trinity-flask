"""
Route Request Decorators.

Provides JSON request validation decorators using Pydantic DTO models.
"""

from functools import wraps
from typing import Type
from flask import request
from pydantic import BaseModel

from app.domain.errors import ValidationError


def validate_json(schema: Type[BaseModel]):
    """
    Decorator that validates incoming JSON payload against a Pydantic schema
    and passes the validated model to the endpoint function as its first positional argument.

    Args:
        schema (Type[BaseModel]): Target Pydantic schema class.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json(silent=True)
            if data is None:
                raise ValidationError("REQUEST_BODY_IS_EMPTY")

            # Let Pydantic raise PydanticValidationError to be caught by global error handlers
            validated_data = schema(**data)
            return f(validated_data, *args, **kwargs)

        return decorated_function

    return decorator
