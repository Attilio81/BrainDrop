# tests/test_handlers.py
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from db.models import EnrichedIdea, Idea
from uuid import uuid4
from datetime import datetime


def make_update(text: str, user_id: int = 42):
    update = MagicMock()
    update.effective_user.id = user_id
    update.message.text = text
    update.message.reply_text = AsyncMock()
    return update


def make_context():
    return MagicMock()


def make_fake_idea(**kwargs):
    base = dict(
        id=uuid4(), title="T", summary="S", original_content="raw",
        source_type="text", category="other", tags=[],
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
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai")
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake")


async def test_unauthorized_user_is_ignored(mock_settings):
    from bot.handlers import handle_message
    update = make_update("hello", user_id=999)
    await handle_message(update, make_context())
    update.message.reply_text.assert_not_called()


async def test_authorized_user_gets_response(mock_settings):
    fake_enriched = EnrichedIdea(
        title="Test", summary="Summary.", category="tech",
        source_type="text", tags=["test"], source_url=None, thumbnail_url=None,
    )
    fake_idea = make_fake_idea(title="Test")

    with (
        patch("bot.handlers.coordinator") as mock_coord,
        patch("bot.handlers.db") as mock_db,
    ):
        mock_coord.process = AsyncMock(return_value=fake_enriched)
        mock_db.save_idea = AsyncMock(return_value=fake_idea)

        from bot.handlers import handle_message
        update = make_update("some text", user_id=42)
        await handle_message(update, make_context())

    update.message.reply_text.assert_called()
    call_text = update.message.reply_text.call_args[0][0]
    assert "✅" in call_text


async def test_unauthorized_list_ignored(mock_settings):
    from bot.handlers import handle_list
    update = make_update("/list", user_id=999)
    await handle_list(update, make_context())
    update.message.reply_text.assert_not_called()


async def test_agent_timeout_saves_raw(mock_settings):
    fake_idea = make_fake_idea()

    with (
        patch("bot.handlers.coordinator") as mock_coord,
        patch("bot.handlers.db") as mock_db,
    ):
        mock_coord.process = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_db.save_raw = AsyncMock(return_value=fake_idea)

        from bot.handlers import handle_message
        update = make_update("some text", user_id=42)
        await handle_message(update, make_context())

    update.message.reply_text.assert_called()
    # Last call should be the warning message
    last_call_text = update.message.reply_text.call_args_list[-1][0][0]
    assert "⚠️" in last_call_text
    mock_db.save_raw.assert_called_once()
