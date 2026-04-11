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


async def test_transcribe_returns_text(mock_settings, tmp_path):
    ogg_path = tmp_path / "voice.ogg"
    ogg_path.write_bytes(b"fake-ogg-bytes")

    fake_transcription = MagicMock()
    fake_transcription.text = "Questa è una nota vocale di test."

    with patch("bot.agents.voice.AsyncOpenAI") as MockOpenAI:
        mock_client = AsyncMock()
        MockOpenAI.return_value = mock_client
        mock_client.audio.transcriptions.create = AsyncMock(
            return_value=fake_transcription
        )

        from bot.agents.voice import transcribe
        result = await transcribe(str(ogg_path))

    assert result == "Questa è una nota vocale di test."


async def test_transcribe_returns_none_for_large_file(mock_settings, tmp_path):
    ogg_path = tmp_path / "large.ogg"
    ogg_path.write_bytes(b"x")

    with patch("bot.agents.voice.os.path.getsize", return_value=26 * 1024 * 1024):
        from bot.agents.voice import transcribe
        result = await transcribe(str(ogg_path))

    assert result is None


async def test_transcribe_returns_none_on_api_error(mock_settings, tmp_path):
    ogg_path = tmp_path / "voice.ogg"
    ogg_path.write_bytes(b"fake-ogg-bytes")

    with patch("bot.agents.voice.AsyncOpenAI") as MockOpenAI:
        mock_client = AsyncMock()
        MockOpenAI.return_value = mock_client
        mock_client.audio.transcriptions.create = AsyncMock(
            side_effect=Exception("API error")
        )

        from bot.agents.voice import transcribe
        result = await transcribe(str(ogg_path))

    assert result is None
