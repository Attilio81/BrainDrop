# tests/test_youtube.py
import pytest
from unittest.mock import patch, MagicMock


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


async def test_extract_youtube_returns_payload(mock_settings):
    fake_info = {
        "title": "Come diventare un dev migliore",
        "description": "In questo video esploriamo i fondamentali.",
        "channel": "Dev Italia",
        "duration": 600,
        "thumbnail": "https://i.ytimg.com/vi/abc/hqdefault.jpg",
        "id": "abc123",
    }

    with patch("bot.agents.youtube.yt_dlp.YoutubeDL") as MockYDL:
        mock_ydl = MagicMock()
        MockYDL.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        MockYDL.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info = MagicMock(return_value=fake_info)

        with patch("bot.agents.youtube.YouTubeTranscriptApi") as MockTranscriptApi:
            mock_api_instance = MagicMock()
            MockTranscriptApi.return_value = mock_api_instance
            mock_api_instance.list = MagicMock(side_effect=Exception("no transcript"))

            from bot.agents.youtube import extract
            result = await extract("https://www.youtube.com/watch?v=abc123")

    assert result is not None
    assert "Come diventare un dev migliore" in result["text"]
    assert "Dev Italia" in result["text"]
    assert result["source_url"] == "https://www.youtube.com/watch?v=abc123"
    assert result["thumbnail_url"] == "https://i.ytimg.com/vi/abc/hqdefault.jpg"


async def test_extract_youtube_returns_none_on_error(mock_settings):
    with patch("bot.agents.youtube.yt_dlp.YoutubeDL") as MockYDL:
        mock_ydl = MagicMock()
        MockYDL.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        MockYDL.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info = MagicMock(side_effect=Exception("private video"))

        from bot.agents.youtube import extract
        result = await extract("https://www.youtube.com/watch?v=private")

    assert result is None
