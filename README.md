# BrainDrop

Personal knowledge capture system via Telegram. Send a link, text, Instagram post, photo, voice note, or YouTube URL — BrainDrop enriches it with AI and saves it to your personal knowledge base.

## What it does

| Input | What happens |
|---|---|
| URL | Scrapes the page (Firecrawl) + Tavily context → structured entry |
| Plain text | Tavily enrichment → structured entry |
| Instagram URL | Downloads post via instaloader, OCR on each slide (GPT-4o-mini) → structured entry |
| Telegram photo | GPT-4o-mini Vision description/OCR → structured entry |
| Voice note | OpenAI Whisper transcription → structured entry |
| YouTube URL | yt-dlp metadata + transcript → structured entry |

Every entry gets: English title, Italian summary, category, tags, source URL, thumbnail. Stored in Supabase.

## Architecture

```
Telegram bot (python-telegram-bot)
    ↓
Media extractors (instagram / photo / voice / youtube)
    ↓
Agno coordinator (DeepSeek R1 + Tavily + Firecrawl)
    ↓
Supabase (PostgreSQL + RLS)
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/Attilio81/BrainDrop.git
cd BrainDrop
pip install -r requirements.txt
```

### 2. Environment variables

Copy `.env.example` to `.env` and fill in all values:

```bash
cp .env.example .env
```

| Variable | Where to get it |
|---|---|
| `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/BotFather) on Telegram |
| `AUTHORIZED_USER_ID` | Your Telegram user ID (send `/start` to [@userinfobot](https://t.me/userinfobot)) |
| `DEEPSEEK_API_KEY` | [platform.deepseek.com](https://platform.deepseek.com) |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) |
| `FIRECRAWL_API_KEY` | [firecrawl.dev](https://firecrawl.dev) |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) — used for Whisper (voice) and GPT-4o-mini (OCR) |
| `SUPABASE_URL` | Supabase project Settings → API |
| `SUPABASE_SERVICE_KEY` | Supabase project Settings → API → service_role key |

### 3. Supabase — run migrations

In **Supabase Dashboard → SQL Editor**, run in order:

1. `db/migrations/001_initial.sql` — creates the `ideas` table
2. `db/migrations/002_phase2.sql` — updates the `source_type` constraint (no-op if running fresh)

### 4. Run the bot

```bash
python -m bot.main
```

## Telegram commands

| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/list` | Last 10 saved entries |
| `/publish_<id>` | Toggle publish/hide an entry |
| `/delete_<id>` | Soft-delete an entry |

Send any message (text, URL, Instagram link, YouTube link, photo, voice note) and the bot processes it automatically.

## Project structure

```
braindrop/
├── bot/
│   ├── agents/
│   │   ├── coordinator.py    # Agno agent (DeepSeek R1 + Tavily + Firecrawl)
│   │   ├── instagram.py      # instaloader + GPT-4o-mini OCR
│   │   ├── photo.py          # GPT-4o-mini Vision
│   │   ├── voice.py          # OpenAI Whisper
│   │   ├── youtube.py        # yt-dlp + youtube-transcript-api
│   │   └── tools.py          # Firecrawl scrape_url tool
│   ├── handlers.py           # Telegram message handlers
│   ├── config.py             # pydantic-settings
│   └── main.py               # Entry point
├── db/
│   ├── client.py             # Supabase async wrapper
│   ├── models.py             # Pydantic models
│   └── migrations/
│       ├── 001_initial.sql
│       └── 002_phase2.sql
├── tests/                    # 36 tests, all passing
├── .env.example
├── Dockerfile
└── requirements.txt
```

## Running tests

```bash
python -m pytest -v
```

36 tests, no external API calls (all mocked).

## Roadmap

- **Phase 1** ✅ — Text, URLs, Telegram bot, Supabase
- **Phase 2** ✅ — Instagram, photos, voice notes, YouTube, Italian summaries
- **Phase 3** — Admin panel
- **Phase 4** — Public frontend
- **Phase 5** — Semantic search (pgvector)
