"""
Application Factory Module.

Configures and initializes the Flask application instance, including database setup,
dependency injection container, event subscriptions, error handling, and routing.
"""

import os
from flask import Flask
from flask_migrate import Migrate

from app.storage.sqlalchemy.db import db
from app.config import DevelopmentConfig, ProductionConfig, TestingConfig
from app.containers import Container
from app.routes import register_routes
from app.errors import register_error_handlers

# Initialize Flask-Migrate instance for handling database migrations
migrate = Migrate()


def create_app() -> Flask:
    """
    Application factory function for creating and configuring the Flask app.

    Returns:
        Flask: The fully configured Flask application instance.
    """
    flask_app = Flask(__name__)
    env = os.getenv("FLASK_ENV", "development").lower()

    # Load configuration based on the target environment
    if env == "production":
        flask_app.config.from_object(ProductionConfig)
        ProductionConfig.init_app(flask_app)
    elif env == "testing":
        flask_app.config.from_object(TestingConfig)
        TestingConfig.init_app(flask_app)
    else:
        flask_app.config.from_object(DevelopmentConfig)
        DevelopmentConfig.init_app(flask_app)

    # Initialize Dependency Injection Container
    container = Container()
    container.config.from_dict(flask_app.config)
    flask_app.container = container

    # Subscribe orchestrator to incoming messaging events
    messaging_service = container.messaging_service()
    orchestrator = container.agent_orchestrator()
    messaging_service.subscribe(orchestrator.handle_incoming_message)

    # Initialize SQLAlchemy database and migration engine
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    # Register SQLAlchemy models to ensure metadata registration
    import app.storage.sqlalchemy.models

    # Register error handlers and API routes
    register_error_handlers(flask_app)
    register_routes(flask_app, container)

    return flask_app
