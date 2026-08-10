"""
Global Error Handling Module.

Registers central error handlers to intercept domain exceptions and return standard HTTP JSON responses.
"""

import logging
from flask import Flask, jsonify
from pydantic import ValidationError as PydanticValidationError

from app.domain.errors import DomainError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """
    Registers custom application exception handlers on the Flask app.

    Args:
        app (Flask): The target Flask application instance.
    """

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        """Catches domain validation errors and returns HTTP 400 Bad Request."""
        response = jsonify({
            "error": "VALIDATION_ERROR",
            "message": error.message,
            "details": error.details,
        })
        response.status_code = 400
        return response

    @app.errorhandler(PydanticValidationError)
    def handle_pydantic_validation_error(error: PydanticValidationError):
        """Catches request schema validation errors and returns HTTP 400 Bad Request."""
        formatted_errors = [
            {"field": " -> ".join(map(str, err["loc"])), "message": err["msg"]}
            for err in error.errors()
        ]
        response = jsonify({
            "error": "INVALID_REQUEST_PAYLOAD",
            "message": "Input validation failed for request payload.",
            "details": formatted_errors,
        })
        response.status_code = 400
        return response

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error: NotFoundError):
        """Catches missing entity errors and returns HTTP 404 Not Found."""
        response = jsonify({
            "error": "NOT_FOUND",
            "message": error.message,
            "details": error.details,
        })
        response.status_code = 404
        return response

    @app.errorhandler(DomainError)
    def handle_generic_domain_error(error: DomainError):
        """Catches unhandled domain logic errors and returns HTTP 400 Bad Request."""
        response = jsonify({
            "error": "DOMAIN_ERROR",
            "message": error.message,
            "details": error.details,
        })
        response.status_code = 400
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        """Catches unexpected exceptions and returns HTTP 500 Internal Server Error."""
        app.logger.error(f"Unexpected application error: {error}", exc_info=True)

        response = jsonify({
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred.",
            "details": [],
        })
        response.status_code = 500
        return response
