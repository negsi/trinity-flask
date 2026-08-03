"""
Application Entry Point.

Creates the Flask application instance using the application factory pattern
and starts the development web server when executed directly.
"""

from app import create_app

# Instantiate the Flask application via the factory function
app = create_app()

if __name__ == "__main__":
    # Start the Flask development server
    app.run()
