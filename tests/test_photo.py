# tests/test_photo.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


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


async def test_extract_photo_returns_description(mock_settings, tmp_path):
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"fake-image-bytes")

    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {
        "choices": [{"message": {"content": "A slide with the text /SPY"}}]
    }

    with patch("bot.agents.photo.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=fake_response)
        MockClient.return_value = mock_client

        from bot.agents.photo import extract
        result = await extract(str(img_path))

    assert result == "A slide with the text /SPY"


async def test_extract_photo_returns_none_on_api_error(mock_settings, tmp_path):
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"fake-image-bytes")

    with patch("bot.agents.photo.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=Exception("API error"))
        MockClient.return_value = mock_client

        from bot.agents.photo import extract
        result = await extract(str(img_path))

    assert result is None
