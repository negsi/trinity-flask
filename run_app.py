"""
Application Entry Point.

Creates the Flask application instance using the application factory pattern
and starts the development web server when executed directly.
"""

import os
from app import create_app

# Instantiate the Flask application via the factory function
app = create_app()

if __name__ == "__main__":
    # Start embedded background scheduler unless disabled via environment variable.
    # Guard against duplicate execution when Flask debug reloader is active.
    scheduler_embedded = (
        os.getenv("SCHEDULER_EMBEDDED", "true").lower() in ("true", "1", "yes")
    )
    if scheduler_embedded and (
        os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug
    ):
        runner = app.container.schedule_runner()
        runner.start_background(app=app)

    # Start the Flask development server
    app.run()