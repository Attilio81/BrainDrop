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


def test_transcribe_reel_returns_text_on_success(mock_settings):
    from bot.agents.instagram import _transcribe_reel

    mock_download_resp = MagicMock()
    mock_download_resp.raise_for_status = MagicMock()
    mock_download_resp.content = b"fake-mp4-bytes"

    mock_whisper_resp = MagicMock()
    mock_whisper_resp.raise_for_status = MagicMock()
    mock_whisper_resp.json = MagicMock(return_value={"text": "First tip. Second tip."})

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get = MagicMock(return_value=mock_download_resp)
    mock_client.post = MagicMock(return_value=mock_whisper_resp)

    with patch("bot.agents.instagram.httpx.Client", return_value=mock_client):
        result = _transcribe_reel("https://cdn.instagram.com/reel.mp4", "fake-key")

    assert result == "First tip. Second tip."


def test_transcribe_reel_returns_empty_on_download_error(mock_settings):
    from bot.agents.instagram import _transcribe_reel

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get = MagicMock(side_effect=Exception("connection error"))

    with patch("bot.agents.instagram.httpx.Client", return_value=mock_client):
        result = _transcribe_reel("https://cdn.instagram.com/reel.mp4", "fake-key")

    assert result == ""


def test_transcribe_reel_returns_empty_on_whisper_error(mock_settings):
    from bot.agents.instagram import _transcribe_reel

    mock_download_resp = MagicMock()
    mock_download_resp.raise_for_status = MagicMock()
    mock_download_resp.content = b"fake-mp4-bytes"

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get = MagicMock(return_value=mock_download_resp)
    mock_client.post = MagicMock(side_effect=Exception("whisper error"))

    with patch("bot.agents.instagram.httpx.Client", return_value=mock_client):
        result = _transcribe_reel("https://cdn.instagram.com/reel.mp4", "fake-key")

    assert result == ""
