# 🧠 BrainDrop

> **Cattura tutto. Dimentica niente.**

BrainDrop è il tuo secondo cervello personale via Telegram. Mandi un link, un post Instagram, una foto, una nota vocale o un'idea — lui la analizza, la arricchisce con AI e la salva nella tua knowledge base.

---

## ✨ Come funziona

```
Tu mandi qualcosa su Telegram
        ↓
BrainDrop estrae il contenuto
        ↓
DeepSeek R1 analizza e arricchisce
        ↓
Salvato in Supabase, pronto da consultare
```

---

## 📥 Cosa puoi mandare

| Input | Cosa succede |
|---|---|
| 🔗 **URL / articolo** | Scraping (Firecrawl) + contesto (Tavily) → entry strutturata |
| 📸 **Post Instagram** | Caption + OCR di ogni slide del carosello (GPT-4o-mini) → testo completo |
| ▶️ **Video YouTube** | Metadati + trascrizione automatica → riassunto |
| 🖼 **Foto Telegram** | Descrizione visiva + OCR (GPT-4o-mini) → testo |
| 🎙 **Nota vocale** | Trascrizione (OpenAI Whisper) → testo |
| 💬 **Testo libero** | Ricerca Tavily per contesto → entry arricchita |

Ogni entry riceve: **titolo in inglese**, **riassunto narrativo in italiano**, **categoria**, **tag**, **URL sorgente**.

---

## 🤖 Stack tecnico

| Layer | Tecnologia |
|---|---|
| Bot | python-telegram-bot |
| Reasoning | DeepSeek R1 via Agno |
| Web search | Tavily |
| Web scraping | Firecrawl |
| Vision / OCR | GPT-4o-mini (OpenAI) |
| Voice | Whisper (OpenAI) |
| Instagram | instaloader |
| YouTube | yt-dlp + youtube-transcript-api |
| Database | Supabase (PostgreSQL + RLS) |

---

## 🚀 Setup

### 1. Clona e installa

```bash
git clone https://github.com/Attilio81/BrainDrop.git
cd BrainDrop
pip install -r requirements.txt
```

### 2. Variabili d'ambiente

```bash
cp .env.example .env
# Apri .env e compila tutti i valori
```

| Variabile | Dove trovarla |
|---|---|
| `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/BotFather) |
| `AUTHORIZED_USER_ID` | Il tuo ID Telegram → [@userinfobot](https://t.me/userinfobot) |
| `DEEPSEEK_API_KEY` | [platform.deepseek.com](https://platform.deepseek.com) |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) |
| `FIRECRAWL_API_KEY` | [firecrawl.dev](https://firecrawl.dev) |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) — Whisper + Vision OCR |
| `SUPABASE_URL` | Supabase → Settings → API |
| `SUPABASE_SERVICE_KEY` | Supabase → Settings → API → `service_role` |

### 3. Supabase — esegui le migrazioni

In **Supabase Dashboard → SQL Editor**, esegui in ordine:

```sql
-- 1. Crea la tabella ideas
-- (incolla il contenuto di db/migrations/001_initial.sql)

-- 2. Aggiorna il vincolo source_type
-- (incolla il contenuto di db/migrations/002_phase2.sql)
```

### 4. Avvia il bot

**Windows:** doppio click su `start.bat`

**Terminale:**
```bash
python -m bot.main
```

---

## 💬 Comandi Telegram

| Comando | Descrizione |
|---|---|
| `/start` | Mostra il messaggio di benvenuto |
| `/list` | Ultimi 10 elementi salvati |
| `/publish_<id>` | Pubblica o nascondi un elemento |
| `/delete_<id>` | Elimina (soft delete) |
| `/clear` | 🗑 Svuota tutto il database |

---

## 🗂 Struttura del progetto

```
BrainDrop/
├── bot/
│   ├── agents/
│   │   ├── coordinator.py    # Agno agent — DeepSeek R1 + Tavily + Firecrawl
│   │   ├── instagram.py      # instaloader + GPT-4o-mini OCR
│   │   ├── photo.py          # GPT-4o-mini Vision
│   │   ├── voice.py          # OpenAI Whisper
│   │   ├── youtube.py        # yt-dlp + trascrizioni
│   │   └── tools.py          # Firecrawl tool per Agno
│   ├── handlers.py           # Handler Telegram
│   ├── config.py             # Configurazione (pydantic-settings)
│   └── main.py               # Entry point
├── db/
│   ├── client.py             # Wrapper Supabase async
│   ├── models.py             # Modelli Pydantic
│   └── migrations/
│       ├── 001_initial.sql   # Schema iniziale
│       └── 002_phase2.sql    # Aggiornamento source_type
├── tests/                    # 36 test, tutti in verde ✅
├── start.bat                 # Avvio rapido Windows
├── .env.example
└── Dockerfile
```

---

## 🛣 Roadmap

- ✅ **Phase 1** — Testo, URL, bot Telegram, Supabase
- ✅ **Phase 2** — Instagram, foto, note vocali, YouTube, riassunti in italiano
- ⬜ **Phase 3** — Admin panel
- ⬜ **Phase 4** — Frontend pubblico
- ⬜ **Phase 5** — Ricerca semantica (pgvector)
