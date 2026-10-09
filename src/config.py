"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    WEBHOOK_SECRET: str = ""
    GITHUB_TOKEN: str = ""
    GROQ_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    MAX_ITERATIONS: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
