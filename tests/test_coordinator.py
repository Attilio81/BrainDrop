import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from db.models import EnrichedIdea
from bot.agents.coordinator import Coordinator


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake")
    monkeypatch.setenv("AUTHORIZED_USER_ID", "1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake")
    monkeypatch.setenv("TAVILY_API_KEY", "fake")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fake")
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai")


async def test_coordinator_returns_enriched_idea(mock_settings):
    fake_idea = EnrichedIdea(
        title="Test Title",
        summary="A test summary.",
        category="tech",
        source_type="url",
        tags=["test"],
        source_url="https://example.com",
        thumbnail_url=None,
    )
    fake_response = MagicMock()
    fake_response.content = fake_idea

    with patch("bot.agents.coordinator.Agent") as MockAgent:
        instance = AsyncMock()
        instance.arun = AsyncMock(return_value=fake_response)
        MockAgent.return_value = instance

        coord = Coordinator()
        result = await coord.process("https://example.com")

    assert isinstance(result, EnrichedIdea)
    assert result.title == "Test Title"
    assert result.category == "tech"


def test_system_prompt_requests_italian_summary():
    from bot.agents.coordinator import SYSTEM_PROMPT
    assert "ITALIAN" in SYSTEM_PROMPT or "italiano" in SYSTEM_PROMPT.lower()
