# tests/test_db_client.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

FAKE_UUID = str(uuid4())

def make_fake_row(**kwargs):
    base = {
        "id": FAKE_UUID,
        "created_at": datetime.now().isoformat(),
        "title": "Test",
        "summary": "Summary",
        "original_content": "content",
        "source_type": "text",
        "category": "other",
        "tags": [],
        "source_url": None,
        "thumbnail_url": None,
        "enrichment_data": {},
        "published": False,
        "published_at": None,
        "deleted_at": None,
    }
    base.update(kwargs)
    return base


@pytest.fixture
def mock_supabase():
    with patch("db.client.acreate_client") as mock_create:
        client = AsyncMock()
        mock_create.return_value = client

        table = MagicMock()
        client.table = MagicMock(return_value=table)

        insert_chain = MagicMock()
        table.insert.return_value = insert_chain
        insert_chain.execute = AsyncMock(return_value=MagicMock(data=[make_fake_row()]))

        select_chain = MagicMock()
        table.select.return_value = select_chain
        select_chain.is_.return_value = select_chain
        select_chain.eq.return_value = select_chain
        select_chain.like.return_value = select_chain
        select_chain.order.return_value = select_chain
        select_chain.limit.return_value = select_chain
        select_chain.execute = AsyncMock(return_value=MagicMock(data=[make_fake_row()]))

        update_chain = MagicMock()
        table.update.return_value = update_chain
        update_chain.like.return_value = update_chain
        update_chain.execute = AsyncMock(return_value=MagicMock(data=[make_fake_row(published=True)]))

        yield client


async def test_save_idea(mock_supabase):
    from db.client import SupabaseClient
    from db.models import IdeaCreate
    c = SupabaseClient(supabase=mock_supabase)
    idea = IdeaCreate(
        title="Test", summary="Sum", original_content="raw",
        source_type="text", category="other", tags=[]
    )
    result = await c.save_idea(idea)
    assert result.title == "Test"


async def test_list_ideas(mock_supabase):
    from db.client import SupabaseClient
    c = SupabaseClient(supabase=mock_supabase)
    results = await c.list_ideas()
    assert len(results) == 1


async def test_toggle_publish(mock_supabase):
    from db.client import SupabaseClient
    c = SupabaseClient(supabase=mock_supabase)
    result = await c.toggle_publish("abc12345")
    assert result.published is True
