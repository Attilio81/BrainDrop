# BrainDrop — Phase 1 Design (MVP Bot)

**Data:** 2026-04-11  
**Scope:** Phase 1 — Telegram bot (polling) + single Agno agent + Supabase. Input: testo e URL. Comandi: `/list`, `/publish`, `/delete`.  
**Fasi successive:** Phase 2 (photo, voice, YouTube/Instagram, multi-agent), Phase 3 (admin panel), Phase 4 (frontend pubblico), Phase 5 (semantic search).

---

## 1. Struttura del Progetto

```
braindrop/
├── bot/
│   ├── main.py              # Entry point polling mode
│   ├── handlers.py          # Message + command handlers
│   ├── config.py            # Pydantic Settings (env vars)
│   └── agents/
│       └── coordinator.py   # Single Agno agent
├── db/
│   ├── client.py            # Supabase async wrapper
│   ├── models.py            # Pydantic models (IdeaCreate, Idea)
│   └── migrations/
│       └── 001_initial.sql  # Schema completo
├── .env.example
├── requirements.txt
└── Dockerfile
```

---

## 2. Configurazione (`config.py`)

Usa `pydantic-settings`, singleton via `lru_cache`.

**Variabili d'ambiente:**

```env
# Telegram
TELEGRAM_BOT_TOKEN=
AUTHORIZED_USER_ID=          # int — unico utente autorizzato

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

---

## 3. Telegram Bot Layer (`handlers.py`)

### Guardia di autenticazione
Ogni handler controlla `update.effective_user.id == settings.AUTHORIZED_USER_ID`. Se non corrisponde: silenzio, nessuna risposta.

### Handler messaggi (testo e URL)

1. Invia subito `⏳ Elaborazione in corso...` come feedback
2. Chiama `asyncio.wait_for(coordinator.arun(text), timeout=settings.AGENT_TIMEOUT_SECONDS)`
3. Se successo → salva su Supabase → risponde:

```
✅ Salvato: {title}
📂 {category} | 🏷 {tags}
📝 {summary}
🔗 /publish_{id[:8]}
```

4. Se timeout o eccezione → `save_raw()` → risponde `⚠️ Salvato senza arricchimento (id: {id[:8]}). Riprova a inviare il messaggio.`

### Comandi Phase 1

| Comando | Comportamento |
|---------|--------------|
| `/start` | Messaggio di benvenuto |
| `/list` | Ultimi 10 item: `📤 bozza` o `✅ pubblicato`, con short ID |
| `/publish_<id8>` | Toggle published/unpublished, conferma con risposta |
| `/delete_<id8>` | Soft delete (imposta `deleted_at = now()`) |

Gli short ID sono i primi 8 caratteri dell'UUID. Il bot risolve l'UUID completo via `SELECT id WHERE id LIKE '{id8}%'`.

---

## 4. Agno Coordinator Agent (`agents/coordinator.py`)

### Modello
```python
from agno.models.deepseek import DeepSeek
model = DeepSeek(id="deepseek-reasoner")  # R1 con chain-of-thought
```

### Tool
- **`TavilyTools(search_depth="advanced", include_answer=True)`** — ricerca contesto web
- **Custom Firecrawl tool** — wrapping di `firecrawl-py`, attivato solo se l'input contiene un URL. Estrae il contenuto completo della pagina.

### Output strutturato (Pydantic)
```python
class EnrichedIdea(BaseModel):
    title: str
    summary: str          # 2-3 frasi, in inglese
    category: Literal["tech","programming","ai","crossfit",
                       "travel","food","business","personal","other"]
    source_type: Literal["url", "text"]
    tags: list[str]       # max 5, lowercase
    source_url: str | None
    thumbnail_url: str | None
```

### Flusso interno
1. Riceve il testo grezzo
2. Se è un URL → tool Firecrawl estrae contenuto pagina
3. Tool Tavily cerca contesto aggiuntivo
4. Produce `EnrichedIdea` come structured output

### Chiamata async dal handler
```python
response = await asyncio.wait_for(
    coordinator.arun(raw_text),
    timeout=settings.AGENT_TIMEOUT_SECONDS
)
idea: EnrichedIdea = response.content
```

---

## 5. Supabase Schema (`db/`)

### `001_initial.sql`
Schema dal PRD con aggiunte per Phase 1:
- `deleted_at TIMESTAMPTZ` — soft delete attivo da subito
- `notes TEXT` — note private, mai pubbliche
- `embedding VECTOR(1536)` — presente ma non popolato fino a Phase 5

**Policy RLS:**
- Lettura pubblica: `published = true AND deleted_at IS NULL`
- Service role: accesso completo (usato dal bot)

### `db/models.py`

```python
class IdeaCreate(BaseModel):
    title: str
    summary: str
    original_content: str
    source_type: str
    category: str
    tags: list[str]
    source_url: str | None = None
    thumbnail_url: str | None = None

class Idea(IdeaCreate):
    id: UUID
    created_at: datetime
    published: bool
    published_at: datetime | None
    deleted_at: datetime | None
```

### `db/client.py` — metodi principali

| Metodo | Operazione |
|--------|-----------|
| `save_idea(idea: IdeaCreate) → Idea` | INSERT arricchito |
| `save_raw(content, source_type) → Idea` | INSERT fallback grezzo |
| `list_ideas(limit=10) → list[Idea]` | SELECT esclusi soft-deleted |
| `toggle_publish(short_id) → Idea` | UPDATE published + published_at |
| `soft_delete(short_id) → None` | UPDATE deleted_at |
| `resolve_short_id(short_id) → UUID` | SELECT LIKE |

---

## 6. Error Handling

| Scenario | Comportamento |
|----------|--------------|
| Timeout agente | Fallback `save_raw()` → avviso utente |
| Eccezione agente | Fallback `save_raw()` → avviso utente |
| Supabase non raggiungibile | Risposta `❌ Errore database, riprova` |
| URL non scrapabile (Firecrawl) | Agente prosegue con solo Tavily |
| Utente non autorizzato | Silenzio |

Nessun retry automatico in Phase 1 — l'utente reinvia se necessario.

---

## 7. Sviluppo & Deploy

**Locale (test):**
```bash
cp .env.example .env  # compila le variabili
python -m bot.main
```

**Produzione (Railway):**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "bot.main"]
```

Le env vars vengono iniettate dalla Railway dashboard.

---

## 8. Flusso Complessivo

```
Telegram msg
    → auth guard
    → "⏳ Elaborazione..."
    → asyncio.wait_for(coordinator.arun(), timeout=AGENT_TIMEOUT_SECONDS)
        ├── Firecrawl (se URL)
        ├── Tavily (ricerca contesto)
        └── EnrichedIdea (structured output)
    → save_idea(Supabase)
    → risposta formattata con /publish_{id8}

    [in caso di errore]
    → save_raw(Supabase)
    → avviso ⚠️
```

---

## Fuori scope (Phase 1)

- Photo, voice note, YouTube, Instagram
- Multi-agent team (classifier, enricher, summarizer separati)
- Admin panel
- Frontend pubblico /discoveries
- Semantic search / embeddings
- FastAPI layer
