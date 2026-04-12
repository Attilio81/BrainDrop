from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


CATEGORIES = Literal[
    "tech", "programming", "ai", "crossfit",
    "travel", "food", "business", "personal", "other"
]

SOURCE_TYPES = Literal["url", "text"]


class EnrichedIdea(BaseModel):
    """Structured output returned by the Agno coordinator agent."""
    title: str
    summary: str        # narrative prose — context and meaning
    details: str        # schematic bullet list — every specific item, repo, URL, step
    category: CATEGORIES
    source_type: SOURCE_TYPES
    tags: list[str]
    source_url: str | None = None       # optional — LLM may omit
    thumbnail_url: str | None = None    # optional — LLM may omit


class IdeaCreate(BaseModel):
    """Data required to insert a new idea into Supabase."""
    title: str
    summary: str
    details: str = ""
    original_content: str
    # source_type and category are str (not Literal) — validated upstream by EnrichedIdea.
    # Kept loose to allow future categories without code changes.
    source_type: str
    category: str
    tags: list[str]
    source_url: str | None = None
    thumbnail_url: str | None = None
    enrichment_data: dict[str, Any] = Field(default_factory=dict)


class Idea(IdeaCreate):
    """Full idea record as stored in Supabase."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    published: bool = False
    published_at: datetime | None = None
    deleted_at: datetime | None = None
    notes: str | None = None
