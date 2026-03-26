"""Centralized configuration loaded from .env file."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PubMed
    entrez_email: str = "user@example.com"

    # OpenAI
    openai_api_key: str = ""

    # Brave Search
    brave_search_api_key: str = ""

    # KIPRIS
    kipris_api_key: str = ""

    # Google Application
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # CORS
    cors_origins: list[str] = ["*"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
