import pytest
from pydantic import ValidationError
from bot.config import Settings, get_settings


def test_config_requires_telegram_token(monkeypatch):
    """Verifica che TELEGRAM_BOT_TOKEN sia obbligatorio."""
    monkeypatch.setenv("AUTHORIZED_USER_ID", "12345")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake_deepseek")
    monkeypatch.setenv("TAVILY_API_KEY", "fake_tavily")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fake_firecrawl")
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake_service_key")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    missing_fields = [e["loc"] for e in exc_info.value.errors()]
    assert ("TELEGRAM_BOT_TOKEN",) in missing_fields


def test_config_defaults(monkeypatch):
    """Verifica default AGENT_TIMEOUT_SECONDS e type conversion AUTHORIZED_USER_ID."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake_token")
    monkeypatch.setenv("AUTHORIZED_USER_ID", "12345")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake_deepseek")
    monkeypatch.setenv("TAVILY_API_KEY", "fake_tavily")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fake_firecrawl")
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake_service_key")
    s = Settings(_env_file=None)
    assert s.AGENT_TIMEOUT_SECONDS == 60
    assert s.AUTHORIZED_USER_ID == 12345


def test_get_settings_returns_singleton(monkeypatch):
    """Verifica che get_settings() ritorni sempre la stessa istanza (lru_cache)."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake_token")
    monkeypatch.setenv("AUTHORIZED_USER_ID", "1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake_deepseek")
    monkeypatch.setenv("TAVILY_API_KEY", "fake_tavily")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fake_firecrawl")
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake_service_key")
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_secret_fields_not_exposed_in_repr(monkeypatch):
    """Verifica che i campi SecretStr non siano visibili nel repr."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "super_secret_token")
    monkeypatch.setenv("AUTHORIZED_USER_ID", "1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-secret")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-secret")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-secret")
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "sk-supabase-secret")
    s = Settings(_env_file=None)
    repr_str = repr(s)
    assert "super_secret_token" not in repr_str
    assert "sk-secret" not in repr_str
