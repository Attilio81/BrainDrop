# BrainDrop Phase 1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Telegram bot (polling mode) that receives text and URLs, enriches them via a single Agno agent (DeepSeek R1 + Tavily + Firecrawl), and saves them to Supabase — with `/list`, `/publish`, and `/delete` commands.

**Architecture:** Auth-guarded PTB handlers receive messages → call an async Agno coordinator agent with a 60-second timeout → save the `EnrichedIdea` structured output to Supabase. On failure, a raw fallback is saved. Dynamic commands (`/publish_<id8>`, `/delete_<id8>`) are matched via regex handlers.

**Tech Stack:** `python-telegram-bot>=21`, `agno` (latest), `supabase>=2`, `pydantic-settings>=2`, `tavily-python`, `firecrawl-py`, `pytest`, `pytest-asyncio`

---

## File Map

```
braindrop/
├── bot/
│   ├── __init__.py             # empty
│   ├── config.py               # Pydantic Settings — all env vars
│   ├── main.py                 # Application builder + handler registration + run_polling
│   ├── handlers.py             # Auth guard + message handler + command handlers
│   └── agents/
│       ├── __init__.py         # empty
│       ├── coordinator.py      # Coordinator class wrapping Agno Agent
│       └── tools.py            # Custom Firecrawl scrape_url tool function
├── db/
│   ├── __init__.py             # empty
│   ├── models.py               # IdeaCreate, Idea, EnrichedIdea (Pydantic)
│   ├── client.py               # SupabaseClient async wrapper
│   └── migrations/
│       └── 001_initial.sql     # Full schema + RLS policies
├── tests/
│   ├── __init__.py             # empty
│   ├── conftest.py             # Clears lru_cache between tests
│   ├── test_config.py          # Config validation tests
│   ├── test_models.py          # Pydantic model validation tests
│   ├── test_db_client.py       # DB client tests (mocked Supabase)
│   ├── test_coordinator.py     # Coordinator tests (mocked Agno)
│   └── test_handlers.py        # Handler tests (mocked PTB + Coordinator)
├── .env.example
├── requirements.txt
├── pytest.ini
└── Dockerfile
```

---

## Task 1: Project Bootstrap

**Files:**
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `.env.example`
- Create: `bot/__init__.py`, `bot/agents/__init__.py`, `db/__init__.py`, `tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p bot/agents db/migrations tests
touch bot/__init__.py bot/agents/__init__.py db/__init__.py tests/__init__.py tests/conftest.py
```

Write `tests/conftest.py` — clears the `get_settings` lru_cache between tests so monkeypatched env vars always take effect:

```python
# tests/conftest.py
import pytest
from bot.config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
```

- [ ] **Step 2: Write `requirements.txt`**

```
python-telegram-bot>=21.0
agno
supabase>=2.0.0
pydantic-settings>=2.0.0
tavily-python
firecrawl-py
httpx
pytest
pytest-asyncio
```

- [ ] **Step 3: Write `pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 4: Write `.env.example`**

```env
# Telegram
TELEGRAM_BOT_TOKEN=
AUTHORIZED_USER_ID=

# DeepSeek
DEEPSEEK_API_KEY=

# Ricerca e scraping
TAVILY_API_KEY=
FIRECRAWL_API_KEY=

# Supabase
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
# SUPABASE_ANON_KEY=     # Phase 4 — frontend pubblico

# Agente
AGENT_TIMEOUT_SECONDS=60
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 6: Commit**

```bash
git init
git add .
git commit -m "chore: project bootstrap — requirements, structure, .env.example"
```

---

## Task 2: Config Module

**Files:**
- Create: `bot/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import pytest
from pydantic import ValidationError

def test_config_requires_telegram_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    from importlib import reload
    import bot.config as cfg
    with pytest.raises((ValidationError, Exception)):
        cfg.Settings()

def test_config_defaults(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake_token")
    monkeypatch.setenv("AUTHORIZED_USER_ID", "12345")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake_deepseek")
    monkeypatch.setenv("TAVILY_API_KEY", "fake_tavily")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fake_firecrawl")
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake_service_key")
    from bot.config import Settings
    s = Settings()
    assert s.AGENT_TIMEOUT_SECONDS == 60
    assert s.AUTHORIZED_USER_ID == 12345
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError` (file doesn't exist yet)

- [ ] **Step 3: Write `bot/config.py`**

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    TELEGRAM_BOT_TOKEN: str
    AUTHORIZED_USER_ID: int

    DEEPSEEK_API_KEY: str
    TAVILY_API_KEY: str
    FIRECRAWL_API_KEY: str

    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str

    AGENT_TIMEOUT_SECONDS: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_config.py -v
```

Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add bot/config.py tests/test_config.py
git commit -m "feat: add config module with pydantic-settings"
```

---

## Task 3: Pydantic Models

**Files:**
- Create: `db/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_models.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Write `db/models.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_models.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add db/models.py tests/test_models.py
git commit -m "feat: add pydantic models (IdeaCreate, Idea, EnrichedIdea)"
```

---

## Task 4: Database Migration

**Files:**
- Create: `db/migrations/001_initial.sql`

- [ ] **Step 1: Write `db/migrations/001_initial.sql`**

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Main ideas table
CREATE TABLE IF NOT EXISTS ideas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Content
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    original_content TEXT NOT NULL,
    enrichment_data JSONB DEFAULT '{}',

    -- Classification
    source_type TEXT NOT NULL CHECK (source_type IN ('url', 'youtube', 'instagram', 'photo', 'voice', 'text')),
    category TEXT NOT NULL DEFAULT 'other',
    tags TEXT[] DEFAULT '{}',

    -- Media
    media_url TEXT,
    source_url TEXT,
    thumbnail_url TEXT,

    -- Publishing
    published BOOLEAN DEFAULT false,
    published_at TIMESTAMPTZ,

    -- Admin (Phase 1+)
    deleted_at TIMESTAMPTZ,
    notes TEXT,
    sort_order INTEGER DEFAULT 0,

    -- Search (Phase 5)
    embedding VECTOR(1536)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ideas_published ON ideas(published, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_ideas_category ON ideas(category);
CREATE INDEX IF NOT EXISTS idx_ideas_tags ON ideas USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_ideas_created ON ideas(created_at DESC);

-- RLS
ALTER TABLE ideas ENABLE ROW LEVEL SECURITY;

-- Public read for published, non-deleted items (Phase 4 frontend)
CREATE POLICY "Public can read published ideas"
    ON ideas FOR SELECT
    USING (published = true AND deleted_at IS NULL);

-- Service role full access (bot)
CREATE POLICY "Service role full access"
    ON ideas FOR ALL
    USING (auth.role() = 'service_role');
```

- [ ] **Step 2: Run migration on Supabase**

  Go to the Supabase Dashboard → SQL Editor → paste the contents of `001_initial.sql` → Run.

  Verify: the `ideas` table appears in Table Editor with all columns.

- [ ] **Step 3: Commit**

```bash
git add db/migrations/001_initial.sql
git commit -m "feat: add Supabase migration 001_initial"
```

---

## Task 5: DB Client

**Files:**
- Create: `db/client.py`
- Create: `tests/test_db_client.py`

- [ ] **Step 1: Write the failing test**

```python
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
        client.table.return_value = table

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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_db_client.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Write `db/client.py`**

```python
from datetime import datetime, timezone

from supabase import acreate_client, AsyncClient

from db.models import Idea, IdeaCreate


class SupabaseClient:
    def __init__(self, supabase: AsyncClient):
        self._db = supabase

    @classmethod
    async def create(cls, url: str, key: str) -> "SupabaseClient":
        client = await acreate_client(url, key)
        return cls(supabase=client)

    async def save_idea(self, idea: IdeaCreate) -> Idea:
        row = idea.model_dump()
        res = await self._db.table("ideas").insert(row).execute()
        return Idea(**res.data[0])

    async def save_raw(self, content: str, source_type: str) -> Idea:
        idea = IdeaCreate(
            title=content[:60] + ("…" if len(content) > 60 else ""),
            summary="(Non elaborato — arricchimento fallito)",
            original_content=content,
            source_type=source_type,
            category="other",
            tags=[],
        )
        return await self.save_idea(idea)

    async def list_ideas(self, limit: int = 10) -> list[Idea]:
        res = (
            await self._db.table("ideas")
            .select("*")
            .is_("deleted_at", "null")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [Idea(**row) for row in res.data]

    async def toggle_publish(self, short_id: str) -> Idea:
        # Fetch current state
        res = (
            await self._db.table("ideas")
            .select("id, published")
            .like("id", f"{short_id}%")
            .execute()
        )
        row = res.data[0]
        new_published = not row["published"]
        update_data: dict = {"published": new_published}
        if new_published:
            update_data["published_at"] = datetime.now(timezone.utc).isoformat()
        else:
            update_data["published_at"] = None

        res2 = (
            await self._db.table("ideas")
            .update(update_data)
            .like("id", f"{short_id}%")
            .execute()
        )
        return Idea(**res2.data[0])

    async def soft_delete(self, short_id: str) -> None:
        await (
            self._db.table("ideas")
            .update({"deleted_at": datetime.now(timezone.utc).isoformat()})
            .like("id", f"{short_id}%")
            .execute()
        )

    async def resolve_short_id(self, short_id: str) -> str:
        res = (
            await self._db.table("ideas")
            .select("id")
            .like("id", f"{short_id}%")
            .execute()
        )
        return res.data[0]["id"]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_db_client.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add db/client.py tests/test_db_client.py
git commit -m "feat: add Supabase async client wrapper"
```

---

## Task 6: Firecrawl Tool

**Files:**
- Create: `bot/agents/tools.py`

No unit test for this tool — it wraps an external API and is best verified in the integration smoke test (Task 9). The function is kept thin on purpose.

- [ ] **Step 1: Write `bot/agents/tools.py`**

```python
import asyncio
import logging

from firecrawl import FirecrawlApp

logger = logging.getLogger(__name__)


def scrape_url(url: str) -> str:
    """
    Scrape the full text content of a URL using Firecrawl.
    Returns markdown content, or empty string on failure.
    Called by the Agno agent as a tool.
    """
    from bot.config import get_settings
    settings = get_settings()
    try:
        app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)
        result = app.scrape_url(url, formats=["markdown"])
        return result.markdown or ""
    except Exception as e:
        logger.warning(f"Firecrawl scraping failed for {url}: {e}")
        return ""
```

> **Note:** `scrape_url` is a sync function. Agno runs tool calls in a thread pool for async agents, so this is safe to use inside an async agent without blocking the event loop.

- [ ] **Step 2: Commit**

```bash
git add bot/agents/tools.py
git commit -m "feat: add Firecrawl scrape_url tool"
```

---

## Task 7: Agno Coordinator Agent

**Files:**
- Create: `bot/agents/coordinator.py`
- Create: `tests/test_coordinator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_coordinator.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from db.models import EnrichedIdea


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake")
    monkeypatch.setenv("AUTHORIZED_USER_ID", "1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake")
    monkeypatch.setenv("TAVILY_API_KEY", "fake")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fake")
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake")


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

        from bot.agents.coordinator import Coordinator
        coord = Coordinator()
        result = await coord.process("https://example.com")

    assert isinstance(result, EnrichedIdea)
    assert result.title == "Test Title"
    assert result.category == "tech"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_coordinator.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Write `bot/agents/coordinator.py`**

```python
from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from agno.tools.tavily import TavilyTools

from bot.agents.tools import scrape_url
from bot.config import get_settings
from db.models import EnrichedIdea

SYSTEM_PROMPT = """You are a personal knowledge assistant. You receive raw text or URLs
and produce structured knowledge entries.

For each input:
1. If it's a URL, use the scrape_url tool to extract its content, then search Tavily for additional context.
2. If it's plain text, search Tavily to find what it refers to and enrich it.
3. Produce a concise English title (max 10 words), a 2-3 sentence English summary explaining
   what it is and why it's interesting, a category from the allowed list, and up to 5 lowercase tags.

Categories: tech, programming, ai, crossfit, travel, food, business, personal, other
Tags: lowercase, max 5, specific (prefer "llm" over "ai", "react" over "javascript")"""


class Coordinator:
    def __init__(self) -> None:
        settings = get_settings()
        self._agent = Agent(
            model=DeepSeek(id="deepseek-reasoner"),
            tools=[
                TavilyTools(search_depth="advanced", include_answer=True),
                scrape_url,
            ],
            instructions=SYSTEM_PROMPT,
            response_model=EnrichedIdea,
        )

    async def process(self, text: str) -> EnrichedIdea:
        response = await self._agent.arun(text)
        return response.content
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_coordinator.py -v
```

Expected: 1 PASSED

- [ ] **Step 5: Commit**

```bash
git add bot/agents/coordinator.py tests/test_coordinator.py
git commit -m "feat: add Agno coordinator agent (DeepSeek R1 + Tavily + Firecrawl)"
```

---

## Task 8: Telegram Handlers

**Files:**
- Create: `bot/handlers.py`
- Create: `tests/test_handlers.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_handlers.py
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_handlers.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Write `bot/handlers.py`**

```python
import asyncio
import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from bot.agents.coordinator import Coordinator
from bot.config import get_settings
from db.client import SupabaseClient
from db.models import IdeaCreate

logger = logging.getLogger(__name__)

# Module-level singletons — initialized in main.py via post_init()
coordinator: Coordinator = None  # type: ignore
db: SupabaseClient = None  # type: ignore

URL_RE = re.compile(r"^https?://\S+$")


def is_authorized(update: Update) -> bool:
    # get_settings() is lru_cache — fast after first call, safe in tests
    return update.effective_user.id == get_settings().AUTHORIZED_USER_ID


def detect_source_type(text: str) -> str:
    return "url" if URL_RE.match(text.strip()) else "text"


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    await update.message.reply_text(
        "👋 BrainDrop attivo!\n\n"
        "Inviami un'idea, un link o un testo — lo salvo e arricchisco automaticamente.\n\n"
        "Comandi:\n"
        "/list — ultimi 10 elementi\n"
        "/publish_<id> — pubblica/nascondi\n"
        "/delete_<id> — elimina"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    text = update.message.text.strip()
    source_type = detect_source_type(text)

    processing_msg = await update.message.reply_text("⏳ Elaborazione in corso...")

    try:
        enriched = await asyncio.wait_for(
            coordinator.process(text),
            timeout=get_settings().AGENT_TIMEOUT_SECONDS,
        )
        idea_create = IdeaCreate(
            title=enriched.title,
            summary=enriched.summary,
            original_content=text,
            source_type=enriched.source_type,
            category=enriched.category,
            tags=enriched.tags,
            source_url=enriched.source_url,
            thumbnail_url=enriched.thumbnail_url,
        )
        saved = await db.save_idea(idea_create)
        short_id = str(saved.id)[:8]
        tags_str = " ".join(f"#{t}" for t in enriched.tags)

        reply = (
            f"✅ Salvato: {enriched.title}\n"
            f"📂 {enriched.category} | 🏷 {tags_str}\n"
            f"📝 {enriched.summary}\n"
            f"🔗 /publish_{short_id}"
        )

    except (asyncio.TimeoutError, Exception) as e:
        logger.error(f"Enrichment failed: {e}")
        saved = await db.save_raw(text, source_type)
        short_id = str(saved.id)[:8]
        reply = f"⚠️ Salvato senza arricchimento (id: {short_id}). Riprova a inviare il messaggio."

    await processing_msg.delete()
    await update.message.reply_text(reply)


async def handle_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    ideas = await db.list_ideas(limit=10)
    if not ideas:
        await update.message.reply_text("Nessun elemento salvato.")
        return

    lines = []
    for idea in ideas:
        status = "✅" if idea.published else "📤"
        short_id = str(idea.id)[:8]
        lines.append(f"{status} {idea.title} — /publish_{short_id} | /delete_{short_id}")

    await update.message.reply_text("\n".join(lines))


async def handle_publish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    text = update.message.text.strip()
    match = re.match(r"^/publish_([a-f0-9]{8})$", text)
    if not match:
        return

    short_id = match.group(1)
    try:
        idea = await db.toggle_publish(short_id)
        status = "✅ Pubblicato" if idea.published else "📤 Nascosto"
        await update.message.reply_text(f"{status}: {idea.title}")
    except Exception as e:
        logger.error(f"Publish toggle failed: {e}")
        await update.message.reply_text("❌ Errore. Riprova.")


async def handle_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    text = update.message.text.strip()
    match = re.match(r"^/delete_([a-f0-9]{8})$", text)
    if not match:
        return

    short_id = match.group(1)
    try:
        await db.soft_delete(short_id)
        await update.message.reply_text(f"🗑 Eliminato ({short_id}).")
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        await update.message.reply_text("❌ Errore. Riprova.")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_handlers.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add bot/handlers.py tests/test_handlers.py
git commit -m "feat: add Telegram handlers (message, list, publish, delete)"
```

---

## Task 9: Bot Entry Point

**Files:**
- Create: `bot/main.py`
- Create: `Dockerfile`

No unit test for `main.py` — it's pure wiring and is validated by the smoke test.

- [ ] **Step 1: Write `bot/main.py`**

```python
import logging

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

import bot.handlers as handlers
from bot.agents.coordinator import Coordinator
from bot.config import get_settings
from db.client import SupabaseClient

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(application):
    """Initialize singletons after event loop is running."""
    settings = get_settings()
    handlers.coordinator = Coordinator()
    handlers.db = await SupabaseClient.create(
        url=settings.SUPABASE_URL,
        key=settings.SUPABASE_SERVICE_KEY,
    )
    logger.info("BrainDrop bot initialized.")


def main() -> None:
    settings = get_settings()

    app = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Static commands
    app.add_handler(CommandHandler("start", handlers.handle_start))
    app.add_handler(CommandHandler("list", handlers.handle_list))

    # Dynamic commands matched via regex (must be before generic text handler)
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^/publish_[a-f0-9]{8}$"),
            handlers.handle_publish,
        )
    )
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^/delete_[a-f0-9]{8}$"),
            handlers.handle_delete,
        )
    )

    # Generic text + URL messages
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message)
    )

    logger.info("Starting BrainDrop bot (polling mode)...")
    app.run_polling()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write `Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "bot.main"]
```

- [ ] **Step 3: Run full test suite**

```bash
pytest -v
```

Expected: all tests PASS (no failures)

- [ ] **Step 4: Commit**

```bash
git add bot/main.py Dockerfile
git commit -m "feat: add bot entry point and Dockerfile"
```

---

## Task 10: Local Smoke Test

No code — manual validation that the bot works end to end.

- [ ] **Step 1: Compile `.env`**

```bash
cp .env.example .env
# Edit .env and fill in all values:
# TELEGRAM_BOT_TOKEN — from @BotFather
# AUTHORIZED_USER_ID — your Telegram numeric user ID (use @userinfobot)
# DEEPSEEK_API_KEY — from platform.deepseek.com
# TAVILY_API_KEY — from app.tavily.com
# FIRECRAWL_API_KEY — from firecrawl.dev
# SUPABASE_URL and SUPABASE_SERVICE_KEY — from Supabase project settings
```

- [ ] **Step 2: Verify migration was applied**

In Supabase Dashboard → Table Editor → confirm `ideas` table exists with all columns.

- [ ] **Step 3: Run the bot**

```bash
python -m bot.main
```

Expected log output:
```
INFO - BrainDrop bot initialized.
INFO - Starting BrainDrop bot (polling mode)...
```

- [ ] **Step 4: Test text input**

In Telegram, send to your bot:
```
Agno è un framework Python per agenti AI multi-step, async e type-safe.
```

Expected bot reply within 60 seconds:
```
✅ Salvato: Agno — Async Python AI Agent Framework
📂 ai | 🏷 #python #ai #agents #agno
📝 Agno is an async-native Python framework...
🔗 /publish_abc12345
```

- [ ] **Step 5: Test URL input**

Send to your bot:
```
https://github.com/agno-agi/agno
```

Expected: bot scrapes the page via Firecrawl, enriches via Tavily, replies with structured output.

- [ ] **Step 6: Test `/list` command**

Send `/list` — expected: list of the 2 saved items with publish/delete links.

- [ ] **Step 7: Test `/publish_<id>` command**

Copy the short ID from Step 4's reply, send `/publish_abc12345` (replace with real ID).
Expected: `✅ Pubblicato: Agno — Async Python AI Agent Framework`

- [ ] **Step 8: Verify in Supabase**

In Supabase Dashboard → Table Editor → `ideas` → confirm rows exist with correct data, and the published row has `published = true`.

- [ ] **Step 9: Final commit**

```bash
git add .
git commit -m "chore: Phase 1 complete — BrainDrop MVP bot"
```

---

## Out of Scope (Phase 1)

- Photo, voice note, YouTube/Instagram handlers
- Multi-agent team (ClassifierAgent, EnricherAgent, SummaryAgent)
- Admin panel (Phase 3)
- Public `/discoveries` frontend (Phase 4)
- Semantic search / embeddings (Phase 5)
- FastAPI layer
- Railway deployment (test locally first)
