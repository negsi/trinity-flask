"""
API Route Blueprint Registration.

Registers API blueprints and wires dependency injection modules.
"""

import importlib
from flask import Flask

ROUTE_MODULES = [
    "app.routes.agents",
    "app.routes.datasources",
    "app.routes.conversations",
    "app.routes.streaming",
    "app.routes.chat",
]


def register_routes(app: Flask, container) -> None:
    """
    Wires dependency container modules and registers Flask blueprints.

    Args:
        app (Flask): Target Flask application instance.
        container: Dependency Injection Container instance.
    """
    # 1. Wire Dependency Injection across all route modules
    container.wire(modules=ROUTE_MODULES)

    # 2. Dynamically import and register blueprints
    for module_path in ROUTE_MODULES:
        module = importlib.import_module(module_path)
        if hasattr(module, "bp"):
            app.register_blueprint(module.bp)
