import pytest
from pydantic import ValidationError
from uuid import UUID, uuid4
from datetime import datetime


def test_idea_create_requires_fields():
    from db.models import IdeaCreate
    with pytest.raises(ValidationError):
        IdeaCreate()  # missing required fields


def test_idea_create_valid():
    from db.models import IdeaCreate
    idea = IdeaCreate(
        title="Test Idea",
        summary="A short summary.",
        original_content="https://example.com",
        source_type="url",
        category="tech",
        tags=["python", "ai"],
    )
    assert idea.tags == ["python", "ai"]
    assert idea.source_url is None
    assert idea.enrichment_data == {}


def test_enriched_idea_category_validation():
    from db.models import EnrichedIdea
    with pytest.raises(ValidationError):
        EnrichedIdea(
            title="Test",
            summary="Summary",
            category="invalid_category",  # not in Literal
            source_type="url",
            tags=[],
        )


def test_enriched_idea_valid():
    from db.models import EnrichedIdea
    idea = EnrichedIdea(
        title="DeepSeek R1",
        summary="A reasoning model by DeepSeek.",
        category="ai",
        source_type="url",
        tags=["ai", "deepseek", "llm"],
        source_url="https://deepseek.com",
    )
    assert idea.category == "ai"
    assert len(idea.tags) == 3
    assert idea.thumbnail_url is None  # optional defaults to None


def test_enriched_idea_optional_fields_default_to_none():
    from db.models import EnrichedIdea
    idea = EnrichedIdea(
        title="Test",
        summary="Summary.",
        category="tech",
        source_type="text",
        tags=[],
    )
    assert idea.source_url is None
    assert idea.thumbnail_url is None


def test_idea_from_supabase_row():
    """Verifica che Idea parsi correttamente un dict come ritornato da Supabase."""
    from db.models import Idea
    fake_row = {
        "id": str(uuid4()),
        "created_at": datetime.now().isoformat(),
        "title": "Test",
        "summary": "Summary",
        "original_content": "raw",
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
    idea = Idea(**fake_row)
    assert isinstance(idea.id, UUID)
    assert idea.published is False


def test_enrichment_data_mutable_default_isolation():
    """Verifica che enrichment_data non condivida lo stesso oggetto dict tra istanze."""
    from db.models import IdeaCreate
    a = IdeaCreate(title="A", summary="S", original_content="c", source_type="text", category="other", tags=[])
    b = IdeaCreate(title="B", summary="S", original_content="c", source_type="text", category="other", tags=[])
    a.enrichment_data["key"] = "value"
    assert "key" not in b.enrichment_data
