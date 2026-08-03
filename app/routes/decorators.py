"""
Route Request Decorators.

Provides Pydantic-based JSON request validation decorators for endpoint functions.
"""

from functools import wraps
from flask import request, jsonify
from pydantic import ValidationError


def validate_json(schema):
    """
    Decorator that validates incoming JSON payload against a Pydantic schema
    and injects the validated DTO into the handler function as the first positional argument.

    Args:
        schema (BaseModel): Target Pydantic schema class.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if data is None:
                return jsonify({"error": "REQUEST_BODY_IS_EMPTY"}), 400
            
            try:
                validated_data = schema(**data)
            except ValidationError as e:
                errors = e.errors()
                formatted_errors = [
                    {"field": " -> ".join(map(str, err["loc"])), "message": err["msg"]}
                    for err in errors
                ]
                return jsonify({"validation_errors": formatted_errors}), 400
            
            return f(validated_data, *args, **kwargs)
        return decorated_function
    return decorator
