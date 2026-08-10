"""
Configuration Management Module.

Defines environment-specific configuration settings for database connections,
LLM providers, upload paths, and application execution parameters.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class BaseConfig:
    """Base configuration class containing shared settings across environments."""

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL_APP")
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False") == "True"
    SQLALCHEMY_TRACK_MODIFICATIONS = (
        os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS", "False") == "True"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": os.getenv("SQLALCHEMY_ENGINE_POOL_PRE_PING", "True") == "True",
        "pool_recycle": int(os.getenv("SQLALCHEMY_ENGINE_POOL_RECYCLE", 280)),
        "pool_size": int(os.getenv("SQLALCHEMY_ENGINE_POOL_SIZE", 5)),
        "max_overflow": int(os.getenv("SQLALCHEMY_ENGINE_MAX_OVERFLOW", 10)),
    }

    # LLM Settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL")

    # File Storage Settings
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER", os.path.join(BASE_DIR, "instance", "uploads")
    )

    SMTP_SERVER = os.getenv("SMTP_SERVER", "localhost")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM = os.getenv("SMTP_FROM", "trinity@localhost")

    @staticmethod
    def init_app(app):
        """Hook for initializing application-specific configuration logic."""
        pass


class DevelopmentConfig(BaseConfig):
    """Development environment configuration with debugging enabled."""

    DEBUG = True

    @staticmethod
    def init_app(app):
        """Attach rich debugging utilities to the development Flask instance."""
        from app.debug import debug
        app.d = debug


class ProductionConfig(BaseConfig):
    """Production environment configuration with optimized performance settings."""

    DEBUG = False
    SQLALCHEMY_ECHO = False

    @staticmethod
    def init_app(app):
        pass


class TestingConfig(BaseConfig):
    """Testing environment configuration utilizing in-memory SQLite storage."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}

    @staticmethod
    def init_app(app):
        pass
