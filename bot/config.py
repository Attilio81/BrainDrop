from functools import lru_cache
from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    TELEGRAM_BOT_TOKEN: SecretStr
    AUTHORIZED_USER_ID: int

    DEEPSEEK_API_KEY: SecretStr
    TAVILY_API_KEY: SecretStr
    FIRECRAWL_API_KEY: SecretStr

    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: SecretStr

    AGENT_TIMEOUT_SECONDS: int = Field(default=60, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
