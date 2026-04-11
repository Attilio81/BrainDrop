# tests/test_instagram.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake")
    monkeypatch.setenv("AUTHORIZED_USER_ID", "42")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake")
    monkeypatch.setenv("TAVILY_API_KEY", "fake")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fake")
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai")


def test_get_shortcode_valid(mock_settings):
    from bot.agents.instagram import _get_shortcode
    assert _get_shortcode("https://www.instagram.com/p/DW2fmbrjP2C/") == "DW2fmbrjP2C"
    assert _get_shortcode("https://www.instagram.com/reel/ABC123xyz/") == "ABC123xyz"


def test_get_shortcode_invalid(mock_settings):
    from bot.agents.instagram import _get_shortcode
    assert _get_shortcode("https://example.com/not-instagram") is None
    assert _get_shortcode("hello world") is None


async def test_extract_returns_none_for_non_instagram_url(mock_settings):
    from bot.agents.instagram import extract
    result = await extract("https://example.com")
    assert result is None


async def test_extract_returns_none_on_instaloader_error(mock_settings):
    from bot.agents.instagram import extract
    with patch("bot.agents.instagram.instaloader.Post.from_shortcode",
               side_effect=Exception("QueryReturnedNotFoundException")):
        result = await extract("https://www.instagram.com/p/DW2fmbrjP2C/")
    assert result is None
