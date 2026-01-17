"""
Configuration management for Spotify DJ application.
Handles API settings and model configurations.
"""
import os
from dotenv import load_dotenv


class LLMConfig:
    """Configuration for LLM (OpenRouter) settings."""

    # OpenRouter API endpoint
    API_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    # Model selection - hardcoded, adjust as needed
    MODEL = "x-ai/grok-code-fast-1"

    # API timeout in seconds
    TIMEOUT = 30

    # API key (loaded from environment via .env)
    API_KEY = None  # Will be set by loading .env

    @classmethod
    def _load_api_key(cls):
        """Load API key from environment (from .env file)."""
        if cls.API_KEY is None:
            load_dotenv()
            cls.API_KEY = os.getenv("OPENROUTER_API_KEY")

    @classmethod
    def get_api_key(cls):
        """Get the OpenRouter API key."""
        cls._load_api_key()
        if not cls.API_KEY:
            raise ValueError(
                "Missing OpenRouter API key. Please set OPENROUTER_API_KEY in .env file."
            )
        return cls.API_KEY

    @classmethod
    def get_model(cls):
        """Get the configured LLM model."""
        return cls.MODEL

    @classmethod
    def get_timeout(cls):
        """Get the API timeout in seconds."""
        return cls.TIMEOUT


class SpotifyConfig:
    """Configuration for Spotify API settings."""

    # Client credentials (loaded from environment)
    CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

    # Required scopes for the application
    SCOPES = [
        "user-read-playback-state",
        "user-modify-playback-state",
    ]

    @classmethod
    def get_credentials(cls):
        """Get Spotify credentials."""
        if not cls.CLIENT_ID or not cls.CLIENT_SECRET:
            raise ValueError(
                "Missing Spotify credentials. Please set SPOTIFY_CLIENT_ID and "
                "SPOTIFY_CLIENT_SECRET in .env file."
            )
        return {
            "client_id": cls.CLIENT_ID,
            "client_secret": cls.CLIENT_SECRET,
            "redirect_uri": cls.REDIRECT_URI,
        }


class JITConfig:
    """Configuration for Just-In-Time queue injection system."""

    # Seconds before song ends to trigger injection
    INJECTION_THRESHOLD = 15

    # Seconds between playback status checks
    POLL_INTERVAL = 1.5

    # Minimum songs to keep in Spotify's queue
    MIN_QUEUE_SIZE = 1

    # Retry attempts for failed injections
    RETRY_ATTEMPTS = 3

    # Delay between retry attempts in seconds
    RETRY_DELAY = 0.5


class AppConfig:
    """General application configuration."""

    # Application name
    APP_NAME = "Spotify DJ"

    # Enable debug mode
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    @classmethod
    def validate_config(cls):
        """
        Validate that all required configuration is present.

        Raises:
            ValueError: If required configuration is missing.
        """
        try:
            LLMConfig.get_api_key()
        except ValueError as e:
            raise ValueError(f"LLM Configuration Error: {e}")

        try:
            SpotifyConfig.get_credentials()
        except ValueError as e:
            raise ValueError(f"Spotify Configuration Error: {e}")
