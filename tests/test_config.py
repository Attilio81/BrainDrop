import pytest
from pydantic import ValidationError


def test_config_requires_telegram_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    from importlib import reload
    import bot.config as cfg
    with pytest.raises((ValidationError, Exception)):
        cfg.Settings(_env_file=None)


def test_config_defaults(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake_token")
    monkeypatch.setenv("AUTHORIZED_USER_ID", "12345")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake_deepseek")
    monkeypatch.setenv("TAVILY_API_KEY", "fake_tavily")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fake_firecrawl")
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake_service_key")
    from bot.config import Settings
    s = Settings(_env_file=None)
    assert s.AGENT_TIMEOUT_SECONDS == 60
    assert s.AUTHORIZED_USER_ID == 12345
