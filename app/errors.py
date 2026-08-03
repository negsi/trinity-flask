"""
Global Error Handling Module.

Registers central error handlers to intercept domain exceptions and return standard HTTP JSON responses.
"""

from flask import Flask, jsonify
from app.domain.errors import ValidationError, NotFoundError


def register_error_handlers(app: Flask):
    """
    Registers custom application exception handlers on the Flask app.

    Args:
        app (Flask): The target Flask application instance.
    """

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Catches domain validation errors and returns HTTP 400 Bad Request."""
        response = jsonify({
            "error": "VALIDATION_ERROR",
            "message": str(error)
        })
        response.status_code = 400
        return response

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error):
        """Catches entity missing errors and returns HTTP 404 Not Found."""
        response = jsonify({
            "error": "NOT_FOUND",
            "message": str(error)
        })
        response.status_code = 404
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Catches unhandled exceptions and returns HTTP 500 Internal Server Error."""
        import traceback
        app.logger.error(f"Unexpected application error: {str(error)}")
        traceback.print_exc()

        response = jsonify({
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred."
        })
        response.status_code = 500
        return response
