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


async def test_extract_success_returns_correct_structure(mock_settings):
    from bot.agents.instagram import extract
    mock_post = MagicMock()
    mock_post.caption = "Test caption"
    mock_post.url = "https://cdn.instagram.com/thumb.jpg"
    mock_post.typename = "GraphImage"
    mock_post.is_video = False

    mock_http_response = MagicMock()
    mock_http_response.raise_for_status = MagicMock()
    mock_http_response.content = b"fake-image-bytes"

    with patch("bot.agents.instagram.instaloader.Post.from_shortcode", return_value=mock_post), \
         patch("bot.agents.instagram._ocr_image", return_value="Slide text here"), \
         patch("bot.agents.instagram.httpx.Client") as MockHttpxClient:
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get = MagicMock(return_value=mock_http_response)
        MockHttpxClient.return_value = mock_client_instance

        result = await extract("https://www.instagram.com/p/DW2fmbrjP2C/")

    assert result is not None
    assert result["source_url"] == "https://www.instagram.com/p/DW2fmbrjP2C/"
    assert result["thumbnail_url"] == "https://cdn.instagram.com/thumb.jpg"
    assert "Caption: Test caption" in result["text"]
    assert "Slide 1:" in result["text"]
