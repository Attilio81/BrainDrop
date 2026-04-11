# BrainDrop — Phase 2 Design (Media Support)

**Data:** 2026-04-11
**Scope:** Phase 2 — Instagram (instaloader + DeepSeek Vision OCR), foto Telegram, voice note (Groq Whisper), YouTube. Summary in italiano. Coordinator Agno invariato.
**Fasi successive:** Phase 3 (admin panel), Phase 4 (frontend pubblico), Phase 5 (semantic search).

---

## 1. Principio Architetturale

L'architettura Phase 1 resta invariata. Si aggiunge un layer di **media extraction** che pre-elabora ogni tipo di media in testo, poi passa al coordinator Agno esistente per l'enrichment.

```
Testo/URL web        →  [Phase 1 invariato]
Instagram URL        →  InstagramExtractor  → caption + OCR slide  →  Coordinator → Supabase
Foto Telegram        →  PhotoExtractor      → descrizione visiva   →  Coordinator → Supabase
Voice note           →  VoiceTranscriber    → trascrizione testo   →  Coordinator → Supabase
YouTube URL          →  YouTubeExtractor    → metadati + trascrizione → Coordinator → Supabase
```

Il coordinator Agno non cambia strutturalmente: riceve sempre testo grezzo e produce `EnrichedIdea`. Cambia solo il `SYSTEM_PROMPT` (summary in italiano) e il fatto che il testo in ingresso può essere più lungo e strutturato (multi-slide).

---

## 2. Struttura del Progetto

```
braindrop/
├── bot/
│   ├── agents/
│   │   ├── coordinator.py      # MODIFICATO: summary in italiano
│   │   ├── tools.py            # invariato (Firecrawl, Tavily)
│   │   ├── instagram.py        # NUOVO: instaloader + DeepSeek VL2 OCR
│   │   ├── photo.py            # NUOVO: foto Telegram → DeepSeek VL2
│   │   ├── voice.py            # NUOVO: OGG → Groq Whisper
│   │   └── youtube.py          # NUOVO: yt-dlp + youtube-transcript-api
│   ├── handlers.py             # MODIFICATO: handle_photo, handle_voice, routing media
│   └── main.py                 # MODIFICATO: registra nuovi handler
├── db/
│   ├── models.py               # MODIFICATO: nuovi source_type
│   └── migrations/
│       └── 002_phase2.sql      # NUOVO: aggiorna CHECK su source_type
├── tests/
│   ├── test_instagram.py       # NUOVO
│   ├── test_photo.py           # NUOVO
│   ├── test_voice.py           # NUOVO
│   ├── test_youtube.py         # NUOVO
│   └── test_handlers_phase2.py # NUOVO: photo + voice handlers
└── requirements.txt            # MODIFICATO: nuove dipendenze
```

---

## 3. Nuove Variabili d'Ambiente

```env
# Aggiunto in Phase 2
GROQ_API_KEY=             # Whisper per voice note (groq.com — gratuito)

# Invariate da Phase 1
TELEGRAM_BOT_TOKEN=
AUTHORIZED_USER_ID=
DEEPSEEK_API_KEY=         # usato sia per testo (R1) che vision (VL2)
TAVILY_API_KEY=
FIRECRAWL_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
AGENT_TIMEOUT_SECONDS=60
```

`INSTALOADER_SESSION_FILE` è opzionale: se impostato, instaloader usa una sessione autenticata (utile per account semi-privati). Non necessario per account pubblici.

---

## 4. Instagram Extractor (`bot/agents/instagram.py`)

### Dipendenze
```
instaloader>=4.10
```

### Flusso
1. Estrai lo shortcode dall'URL (es. `DW2fmbrjP2C` da `/p/DW2fmbrjP2C/`)
2. `instaloader.Post.from_shortcode(loader, shortcode)` — recupera metadati post
3. Per ogni nodo del carosello (o singola immagine):
   - Scarica il file immagine in una directory temp (`tempfile.mkdtemp()`)
   - Invia l'immagine a **DeepSeek VL2** (`deepseek-vl2` via API, compatibile OpenAI)
   - Prompt: `"Extract all visible text from this image. Return only the text, preserving the reading order. If there is no text, return an empty string."`
   - Raccoglie il testo estratto
4. Costruisce il payload testuale:
   ```
   Caption: {post.caption}

   Slide 1:
   {testo_ocr_slide_1}

   Slide 2:
   {testo_ocr_slide_2}
   ...
   ```
5. Cancella la directory temp
6. Ritorna il payload testuale + `source_url` + `thumbnail_url` (prima immagine)

### Gestione errori
| Scenario | Comportamento |
|---|---|
| Post privato | Ritorna `None` → handler chiama `save_raw` con avviso |
| instaloader bloccato (429) | Retry dopo 5s, poi ritorna `None` → fallback |
| Slide senza testo (foto pura) | OCR ritorna `""` → usa solo caption |
| Reel (video) | Salta download video, usa solo caption + thumbnail |

### API DeepSeek VL2
Chiamata diretta via `httpx` (stessa chiave `DEEPSEEK_API_KEY`):
```python
POST https://api.deepseek.com/v1/chat/completions
{
  "model": "deepseek-vl2",
  "messages": [{"role": "user", "content": [
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,{b64}"}},
    {"type": "text", "text": "Extract all visible text..."}
  ]}]
}
```

---

## 5. Photo Extractor (`bot/agents/photo.py`)

### Flusso
1. Riceve `file_path` (percorso locale del file scaricato dall'handler)
2. Invia a DeepSeek VL2:
   - Prompt: `"Describe this image in detail. If it contains text, extract all visible text. Focus on content relevant for a knowledge base entry."`
3. Ritorna la descrizione testuale

### Note
- Usato sia per foto singole inviate via Telegram che per thumbnail/immagini in altri contesti
- `source_type = "photo"`

---

## 6. Voice Transcriber (`bot/agents/voice.py`)

### Dipendenze
```
groq>=0.5.0
```

### Flusso
1. Riceve `file_path` (file `.ogg` scaricato da Telegram)
2. Invia a **Groq Whisper** (`whisper-large-v3-turbo`):
   ```python
   client = Groq(api_key=settings.GROQ_API_KEY.get_secret_value())
   transcription = client.audio.transcriptions.create(
       file=open(file_path, "rb"),
       model="whisper-large-v3-turbo",
       language="it",   # italiano di default, Whisper rileva comunque auto
   )
   ```
3. Ritorna la trascrizione testuale
4. Cancella il file temp

### Gestione errori
| Scenario | Comportamento |
|---|---|
| File troppo grande (>25MB) | Ritorna `None` → fallback `save_raw` |
| Groq non raggiungibile | Eccezione → fallback `save_raw` |

---

## 7. YouTube Extractor (`bot/agents/youtube.py`)

### Dipendenze
```
yt-dlp>=2024.1.0
youtube-transcript-api>=0.6.0
```

### Flusso
1. Estrae metadati con `yt-dlp` (no download video):
   ```python
   ydl_opts = {"quiet": True, "no_warnings": True, "extract_flat": False}
   info = yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=False)
   # → title, description, channel, duration, thumbnail
   ```
2. Tenta di scaricare la trascrizione con `youtube-transcript-api`:
   - Preferisce la lingua italiana se disponibile, poi inglese, poi qualsiasi
3. Costruisce il payload:
   ```
   Title: {title}
   Channel: {channel}
   Duration: {duration}s
   Description: {description}

   Transcript:
   {transcript_text}
   ```
4. Ritorna payload + `source_url` + `thumbnail_url`

### Gestione errori
| Scenario | Comportamento |
|---|---|
| Nessuna trascrizione disponibile | Usa solo metadati (title + description) |
| Video privato/non disponibile | Ritorna `None` → fallback |
| yt-dlp timeout | Eccezione → fallback |

---

## 8. Modifiche al Coordinator (`bot/agents/coordinator.py`)

Unica modifica: aggiornare `SYSTEM_PROMPT` per richiedere il `summary` in italiano.

```python
SYSTEM_PROMPT = """You are a personal knowledge assistant. You receive raw text or URLs
and produce structured knowledge entries.

For each input:
1. If it's a URL, use the scrape_url tool to extract its content, then search Tavily for additional context.
2. If it's plain text, search Tavily to find what it refers to and enrich it.
3. Produce a concise English title (max 10 words), a 2-3 sentence summary IN ITALIAN explaining
   what it is and why it's interesting, a category from the allowed list, and up to 5 lowercase tags.
4. Set source_type to "url" if the input was a URL (starts with http:// or https://), or "text" if it was plain text.

Categories: tech, programming, ai, crossfit, travel, food, business, personal, other
Tags: lowercase, max 5, specific (prefer "llm" over "ai", "react" over "javascript")"""
```

**Nota:** per Instagram, photo, voice, YouTube il `source_type` è già determinato dall'handler. Il valore di `EnrichedIdea.source_type` restituito dal coordinator viene **ignorato** per questi casi — l'handler usa il proprio `source_type` noto quando costruisce `IdeaCreate`. `EnrichedIdea.source_type` resta `Literal["url", "text"]` e serve solo per il flusso URL/testo di Phase 1.

---

## 9. Modifiche agli Handler (`bot/handlers.py`)

### Nuovi handler

**`handle_photo(update, context)`**
1. Auth guard
2. Scarica la foto più grande: `file = await context.bot.get_file(update.message.photo[-1].file_id)`
3. Salva in temp: `await file.download_to_drive(tmp_path)`
4. Chiama `PhotoExtractor.extract(tmp_path)` → testo
5. Passa testo al coordinator con prefisso `[Telegram photo]\n\n{testo}`
6. Salva + risponde come in Phase 1

**`handle_voice(update, context)`**
1. Auth guard
2. Scarica il file OGG: `file = await context.bot.get_file(update.message.voice.file_id)`
3. Salva in temp
4. Chiama `VoiceTranscriber.transcribe(tmp_path)` → testo
5. Passa al coordinator con prefisso `[Voice note]\n\n{testo}`
6. Salva + risponde

### Aggiornamento `handle_message`
Aggiunge rilevamento URL speciali prima di chiamare il coordinator:
```python
if is_instagram_url(text):
    raw_text = await instagram_extractor.extract(text)
    source_type = "instagram"
elif is_youtube_url(text):
    raw_text = await youtube_extractor.extract(text)
    source_type = "youtube"
else:
    raw_text = text  # Phase 1 flow
    source_type = detect_source_type(text)
```

### Aggiornamento `main.py`
```python
app.add_handler(MessageHandler(filters.PHOTO, handlers.handle_photo))
app.add_handler(MessageHandler(filters.VOICE, handlers.handle_voice))
```
(prima del handler testo generico)

---

## 10. Modifiche al DB

### `db/models.py`
```python
SOURCE_TYPES = Literal["url", "text", "instagram", "photo", "voice", "youtube"]
```

### `db/migrations/002_phase2.sql`
```sql
-- Aggiorna il CHECK constraint su source_type per includere i nuovi tipi
ALTER TABLE ideas DROP CONSTRAINT IF EXISTS ideas_source_type_check;
ALTER TABLE ideas ADD CONSTRAINT ideas_source_type_check
    CHECK (source_type IN ('url', 'youtube', 'instagram', 'photo', 'voice', 'text'));
```

---

## 11. Error Handling — Riepilogo

| Scenario | Comportamento |
|---|---|
| Extractor ritorna `None` | Fallback `save_raw(testo_originale)` + avviso ⚠️ |
| Timeout coordinator (60s) | Fallback `save_raw` — invariato da Phase 1 |
| instaloader bloccato | Retry 1x, poi fallback |
| Voice troppo lunga | Fallback immediato |
| YouTube senza trascrizione | Usa solo metadati, procede normalmente |

---

## 12. Priorità Implementazione

1. **Instagram** (fondamentale) — `instagram.py` + aggiornamento `handle_message`
2. **Foto Telegram** — `photo.py` + `handle_photo`
3. **Voice note** — `voice.py` + `handle_voice`
4. **YouTube** — `youtube.py` + aggiornamento `handle_message`
5. **Summary in italiano** — modifica `SYSTEM_PROMPT` coordinator (fatta insieme a Instagram)

---

## Fuori scope (Phase 2)

- Stories Instagram (richiedono sessione autenticata e scadono in 24h)
- Download video Reel completo (solo caption + thumbnail)
- Multi-agent team separato (il coordinator singolo è sufficiente)
- Admin panel (Phase 3)
- Frontend pubblico (Phase 4)
