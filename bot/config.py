from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    TELEGRAM_BOT_TOKEN: str
    AUTHORIZED_USER_ID: int

    DEEPSEEK_API_KEY: str
    TAVILY_API_KEY: str
    FIRECRAWL_API_KEY: str

    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str

    AGENT_TIMEOUT_SECONDS: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
