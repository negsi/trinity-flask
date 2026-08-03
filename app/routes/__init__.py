"""
API Route Blueprint Registration.

Wires dependency injection modules and registers API blueprints with the Flask application.
"""

from flask import Flask
from app.routes.agents import agents_bp
from app.routes.chat import chat_bp


def register_routes(app: Flask, container) -> None:
    """
    Wires dependency container modules and registers Flask blueprints.

    Args:
        app (Flask): Target Flask instance.
        container: Dependency Injection Container instance.
    """
    container.wire(modules=[
        "app.routes.agents",
        "app.routes.chat"
    ])

    app.register_blueprint(agents_bp)
    app.register_blueprint(chat_bp)
