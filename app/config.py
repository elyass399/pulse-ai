from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API Keys
    gemini_api_key: str
    cerebras_api_key: str
    groq_api_key: str

    # Database
    database_url: str = "sqlite:///./pulse.db"

    # App
    app_name: str = "Pulse"
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()