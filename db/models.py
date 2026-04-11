from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


CATEGORIES = Literal[
    "tech", "programming", "ai", "crossfit",
    "travel", "food", "business", "personal", "other"
]

SOURCE_TYPES = Literal["url", "text"]


class EnrichedIdea(BaseModel):
    """Structured output returned by the Agno coordinator agent."""
    title: str
    summary: str
    category: CATEGORIES
    source_type: SOURCE_TYPES
    tags: list[str]
    source_url: str | None
    thumbnail_url: str | None


class IdeaCreate(BaseModel):
    """Data required to insert a new idea into Supabase."""
    title: str
    summary: str
    original_content: str
    source_type: str
    category: str
    tags: list[str]
    source_url: str | None = None
    thumbnail_url: str | None = None
    enrichment_data: dict = {}


class Idea(IdeaCreate):
    """Full idea record as stored in Supabase."""
    id: UUID
    created_at: datetime
    published: bool = False
    published_at: datetime | None = None
    deleted_at: datetime | None = None
