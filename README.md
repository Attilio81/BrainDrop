# 🧠 BrainDrop

> **Cattura tutto. Dimentica niente.**

BrainDrop è il tuo secondo cervello personale via Telegram. Mandi un link, un post Instagram, una foto, una nota vocale o un'idea — lui la analizza, la arricchisce con AI e la salva nella tua knowledge base. Un admin panel React ti permette di gestire, pubblicare e modificare tutto.

---

## ✨ Come funziona

```
Tu mandi qualcosa su Telegram
        ↓
BrainDrop estrae il contenuto
        ↓
DeepSeek R1 analizza e arricchisce
        ↓
Salvato in Supabase, pronto da gestire
        ↓
Admin panel React per pubblicare e modificare
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
| Admin panel | React 19 + Vite 5 + TanStack Query + shadcn/ui |

---

## 🚀 Setup

### 1. Clona e installa (bot)

```bash
git clone https://github.com/Attilio81/BrainDrop.git
cd BrainDrop
pip install -r requirements.txt
```

### 2. Variabili d'ambiente — bot

Crea il file `.env` nella root:

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

### 3. Variabili d'ambiente — admin panel

Crea il file `admin/.env.local`:

```env
VITE_SUPABASE_URL=https://TUO_PROGETTO.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...la_tua_anon_key...
```

### 4. Supabase — esegui le migrazioni

In **Supabase Dashboard → SQL Editor**, esegui in ordine:

```sql
-- 1. Schema iniziale
-- (incolla il contenuto di db/migrations/001_initial.sql)

-- 2. Aggiornamento source_type
-- (incolla il contenuto di db/migrations/002_phase2.sql)

-- 3. Policy RLS per admin panel (utenti autenticati)
-- (incolla il contenuto di db/migrations/003_admin_rls.sql)
```

### 5. Avvia il bot

**Windows:** doppio click su `start.bat`

**Terminale:**
```bash
python -m bot.main
```

### 6. Avvia l'admin panel

**Windows:** doppio click su `start-admin.bat` (installa le dipendenze al primo avvio)

**Terminale:**
```bash
cd admin
npm install   # solo la prima volta
npm run dev
```

Apri [http://localhost:5173](http://localhost:5173), inserisci la tua email e clicca il magic link.

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

## 🖥 Admin Panel

Interfaccia React per gestire la knowledge base:

- **Inbox** — idee salvate, da rivedere e pubblicare
- **Published** — idee pubblicate, visibili al frontend
- **Trash** — idee eliminate, ripristinabili o cancellabili definitivamente

Funzionalità: filtro per testo / categoria / tag, edit modale con titolo, summary, categoria, tag e note private, pulsante Svuota DB.

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
│       ├── 002_phase2.sql    # Aggiornamento source_type
│       └── 003_admin_rls.sql # Policy RLS per admin panel
├── admin/                    # Admin panel React+Vite
│   ├── src/
│   │   ├── App.tsx           # Shell principale + auth guard
│   │   ├── components/       # TabNav, FilterBar, IdeaRow, EditModal, LoginPage
│   │   ├── lib/              # Supabase client + TanStack Query hooks
│   │   └── types.ts          # Tipi condivisi
│   └── .env.local            # Credenziali Supabase (non versionato)
├── start.bat                 # Avvio rapido bot (Windows)
├── start-admin.bat           # Avvio rapido admin panel (Windows)
└── Dockerfile
```

---

## 🛣 Roadmap

- ✅ **Phase 1** — Testo, URL, bot Telegram, Supabase
- ✅ **Phase 2** — Instagram, foto, note vocali, YouTube, riassunti in italiano
- ✅ **Phase 3** — Admin panel React (inbox / published / trash / edit)
- ⬜ **Phase 4** — Frontend pubblico
- ⬜ **Phase 5** — Ricerca semantica (pgvector)
