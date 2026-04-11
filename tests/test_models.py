import pytest
from uuid import UUID
from datetime import datetime

def test_idea_create_requires_fields():
    from db.models import IdeaCreate
    with pytest.raises(Exception):
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

def test_enriched_idea_category_validation():
    from db.models import EnrichedIdea
    with pytest.raises(Exception):
        EnrichedIdea(
            title="Test",
            summary="Summary",
            category="invalid_category",  # not in Literal
            source_type="url",
            tags=[],
            source_url=None,
            thumbnail_url=None,
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
        thumbnail_url=None,
    )
    assert idea.category == "ai"
    assert len(idea.tags) == 3
