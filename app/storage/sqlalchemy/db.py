"""
Database Instance Module.

Instantiates the global Flask-SQLAlchemy object used across database models.
"""

from flask_sqlalchemy import SQLAlchemy

# Global database object
db = SQLAlchemy()
