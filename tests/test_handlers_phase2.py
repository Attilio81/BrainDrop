# tests/test_handlers_phase2.py
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from db.models import EnrichedIdea, Idea
from uuid import uuid4
from datetime import datetime


def make_text_update(text: str, user_id: int = 42):
    update = MagicMock()
    update.effective_user.id = user_id
    update.message.text = text
    update.message.reply_text = AsyncMock()
    return update


def make_photo_update(user_id: int = 42):
    update = MagicMock()
    update.effective_user.id = user_id
    update.message.photo = [MagicMock(file_id="fake_file_id")]
    update.message.reply_text = AsyncMock()
    return update


def make_voice_update(user_id: int = 42):
    update = MagicMock()
    update.effective_user.id = user_id
    update.message.voice = MagicMock(file_id="fake_file_id")
    update.message.reply_text = AsyncMock()
    return update


def make_context():
    ctx = MagicMock()
    mock_file = AsyncMock()
    mock_file.download_to_drive = AsyncMock()
    ctx.bot.get_file = AsyncMock(return_value=mock_file)
    return ctx


def make_fake_idea(source_type="instagram", **kwargs):
    base = dict(
        id=uuid4(), title="T", summary="S", original_content="raw",
        source_type=source_type, category="other", tags=[],
        source_url=None, thumbnail_url=None, enrichment_data={},
        published=False, published_at=None, deleted_at=None,
        created_at=datetime.now(),
    )
    base.update(kwargs)
    return Idea(**base)


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


async def test_instagram_url_routed_through_extractor(mock_settings):
    fake_enriched = EnrichedIdea(
        title="Test Post", summary="Un post di test su AI.",
        category="tech", source_type="url", tags=["test"],
        source_url=None, thumbnail_url=None,
    )
    fake_idea = make_fake_idea(source_type="instagram")
    fake_media = {
        "text": "Caption: Test\n\nSlide 1: Some text",
        "source_url": "https://www.instagram.com/p/DW2fmbrjP2C/",
        "thumbnail_url": None,
    }

    with (
        patch("bot.handlers.coordinator") as mock_coord,
        patch("bot.handlers.db") as mock_db,
        patch("bot.handlers.extract_instagram", new_callable=AsyncMock,
              return_value=fake_media) as mock_ig,
    ):
        mock_coord.process = AsyncMock(return_value=fake_enriched)
        mock_db.save_idea = AsyncMock(return_value=fake_idea)

        from bot.handlers import handle_message
        update = make_text_update("https://www.instagram.com/p/DW2fmbrjP2C/")
        await handle_message(update, make_context())

    mock_ig.assert_called_once_with("https://www.instagram.com/p/DW2fmbrjP2C/")
    last_reply = update.message.reply_text.call_args_list[-1][0][0]
    assert "✅" in last_reply


async def test_instagram_extractor_failure_saves_raw(mock_settings):
    fake_idea = make_fake_idea(source_type="instagram")

    with (
        patch("bot.handlers.db") as mock_db,
        patch("bot.handlers.extract_instagram", new_callable=AsyncMock, return_value=None),
    ):
        mock_db.save_raw = AsyncMock(return_value=fake_idea)

        from bot.handlers import handle_message
        update = make_text_update("https://www.instagram.com/p/DW2fmbrjP2C/")
        await handle_message(update, make_context())

    mock_db.save_raw.assert_called_once()
    last_reply = update.message.reply_text.call_args_list[-1][0][0]
    assert "⚠️" in last_reply


async def test_youtube_url_routed_through_extractor(mock_settings):
    fake_enriched = EnrichedIdea(
        title="Test Video", summary="Un video di test.",
        category="tech", source_type="url", tags=["youtube"],
        source_url=None, thumbnail_url=None,
    )
    fake_idea = make_fake_idea(source_type="youtube")
    fake_media = {
        "text": "Title: Test\nChannel: Dev",
        "source_url": "https://www.youtube.com/watch?v=abc123",
        "thumbnail_url": "https://i.ytimg.com/vi/abc123/hqdefault.jpg",
    }

    with (
        patch("bot.handlers.coordinator") as mock_coord,
        patch("bot.handlers.db") as mock_db,
        patch("bot.handlers.extract_youtube", new_callable=AsyncMock,
              return_value=fake_media) as mock_yt,
    ):
        mock_coord.process = AsyncMock(return_value=fake_enriched)
        mock_db.save_idea = AsyncMock(return_value=fake_idea)

        from bot.handlers import handle_message
        update = make_text_update("https://www.youtube.com/watch?v=abc123")
        await handle_message(update, make_context())

    mock_yt.assert_called_once_with("https://www.youtube.com/watch?v=abc123")
    last_reply = update.message.reply_text.call_args_list[-1][0][0]
    assert "✅" in last_reply
