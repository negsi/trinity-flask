"""
Configuration Management Module.

Defines environment-specific configuration settings for database connections,
LLM providers, image generator providers, upload paths, and application execution parameters.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class BaseConfig:
    """Base configuration class containing shared settings across environments."""

    # Internal API & Network Settings
    # API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")

    # Debugging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL_APP")
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"
    SQLALCHEMY_TRACK_MODIFICATIONS = (
        os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS", "False").lower() == "true"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": os.getenv("SQLALCHEMY_ENGINE_POOL_PRE_PING", "True").lower() == "true",
        "pool_recycle": int(os.getenv("SQLALCHEMY_ENGINE_POOL_RECYCLE", 280)),
        "pool_size": int(os.getenv("SQLALCHEMY_ENGINE_POOL_SIZE", 5)),
        "max_overflow": int(os.getenv("SQLALCHEMY_ENGINE_MAX_OVERFLOW", 10)),
    }

    # LLM Settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

    # Image Generator Settings
    IMAGE_GENERATOR_PROVIDER = os.getenv("IMAGE_GENERATOR_PROVIDER", "gemini")
    IMAGE_GENERATOR_MODEL = os.getenv("IMAGE_GENERATOR_MODEL")

    # File Storage Settings
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER", os.path.join(BASE_DIR, "instance", "uploads")
    )
    CONVERSATIONS_FOLDER = os.getenv(
        "CONVERSATIONS_FOLDER", os.path.join(BASE_DIR, "instance", "conversations")
    )
    MESSAGE_UPLOAD_FOLDER = os.getenv(
        "MESSAGE_UPLOAD_FOLDER", CONVERSATIONS_FOLDER
    )

    # SMTP Mail Settings
    SMTP_SERVER = os.getenv("SMTP_SERVER", "localhost")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM = os.getenv("SMTP_FROM", "trinity@localhost")
    SMTP_TEMPLATE_PATH = os.getenv(
        "SMTP_TEMPLATE_PATH", 
        os.path.join(BASE_DIR, "app", "templates", "base_email.html")
    )

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

        log_level_str = app.config.get("LOG_LEVEL", "DEBUG")
        log_level = getattr(logging, log_level_str, logging.DEBUG)

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            force=True
        )
        app.logger.setLevel(log_level)


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
