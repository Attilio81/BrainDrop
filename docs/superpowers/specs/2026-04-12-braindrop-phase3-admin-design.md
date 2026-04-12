# BrainDrop — Phase 3 Design (Admin Panel)

**Data:** 2026-04-12
**Scope:** Phase 3 — Admin panel locale (React + Vite), accesso diretto a Supabase con service key, nessun deploy. Viste: Inbox / Published / Trash. Azioni: pubblica, annulla pubblicazione, modifica campi, cestina, ripristina, elimina definitivamente.
**Fasi successive:** Phase 4 (frontend pubblico /discoveries), Phase 5 (semantic search).

---

## 1. Principio Architetturale

L'admin panel è un'applicazione React+Vite che gira **esclusivamente in locale** (`npm run dev`). Accede a Supabase tramite la **service_role key** (bypassa RLS — accesso completo a tutte le righe). Non richiede autenticazione utente. Non viene deployato.

```
admin/                  ← React 19 + Vite (locale only)
  └─ @supabase/supabase-js (service_role key)
        └─ Supabase (ideas table)
```

---

## 2. Struttura del Progetto

```
braindrop/
├── admin/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── tsconfig.json
│   ├── package.json
│   ├── .env.local                  # VITE_SUPABASE_URL + VITE_SUPABASE_SERVICE_KEY
│   └── src/
│       ├── main.tsx
│       ├── App.tsx                 # layout root: TabNav + FilterBar + IdeaList
│       ├── lib/
│       │   ├── supabase.ts         # createClient singleton (service key)
│       │   └── queries.ts          # TanStack Query hooks
│       ├── components/
│       │   ├── TabNav.tsx          # Inbox (badge) / Published / Trash
│       │   ├── IdeaRow.tsx         # riga: thumbnail + titolo + meta + azioni
│       │   ├── EditModal.tsx       # Sheet laterale (shadcn) con form di editing
│       │   └── FilterBar.tsx       # search + categoria + tag multi-select
│       └── types.ts                # tipo Idea (mirror di db/models.py)
├── bot/
├── db/
└── …
```

**Avvio:** `cd admin && npm run dev` → `http://localhost:5173`

---

## 3. Dipendenze (`package.json`)

```json
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@supabase/supabase-js": "^2",
    "@tanstack/react-query": "^5",
    "@tanstack/react-query-devtools": "^5",
    "sonner": "^1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4",
    "vite": "^5",
    "typescript": "^5",
    "tailwindcss": "^3",
    "autoprefixer": "^10",
    "postcss": "^8",
    "@types/react": "^19",
    "@types/react-dom": "^19"
  }
}
```

shadcn/ui usato per `Sheet` (drawer laterale) e `Select` — inizializzato con `npx shadcn@latest init`.

---

## 4. Configurazione (`lib/supabase.ts`)

```ts
import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const key = import.meta.env.VITE_SUPABASE_SERVICE_KEY

export const supabase = createClient(url, key)
```

**`.env.local`:**
```env
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_SERVICE_KEY=eyJ...
```

---

## 5. Tipi (`types.ts`)

```ts
export type SourceType = 'url' | 'text' | 'instagram' | 'photo' | 'voice' | 'youtube'

export type Category =
  | 'tech' | 'programming' | 'ai' | 'crossfit'
  | 'travel' | 'food' | 'business' | 'personal' | 'other'

export interface Idea {
  id: string
  created_at: string
  updated_at: string
  title: string
  summary: string
  original_content: string
  enrichment_data: Record<string, unknown>
  source_type: SourceType
  category: Category
  tags: string[]
  media_url: string | null
  source_url: string | null
  thumbnail_url: string | null
  published: boolean
  published_at: string | null
  deleted_at: string | null
  notes: string | null
  sort_order: number
}

export type IdeaPatch = Partial<Pick<Idea,
  'title' | 'summary' | 'category' | 'tags' | 'notes'
>>
```

---

## 6. Query Layer (`lib/queries.ts`)

TanStack Query v5. Tutti gli hook invalidano `['ideas']` dopo una mutazione per mantenere la lista in sync.

### `useIdeas(tab, filters)`

```ts
const useIdeas = (tab: Tab, filters: Filters) => useQuery({
  queryKey: ['ideas', tab, filters],
  queryFn: async () => {
    let q = supabase.from('ideas').select('*').order('created_at', { ascending: false })
    if (tab === 'inbox')     q = q.eq('published', false).is('deleted_at', null)
    if (tab === 'published') q = q.eq('published', true).is('deleted_at', null)
    if (tab === 'trash')     q = q.not('deleted_at', 'is', null)
    if (filters.text)     q = q.or(`title.ilike.%${filters.text}%,summary.ilike.%${filters.text}%`)
    if (filters.category) q = q.eq('category', filters.category)
    if (filters.tags.length) q = q.contains('tags', filters.tags)
    const { data, error } = await q
    if (error) throw error
    return data as Idea[]
  }
})
```

### Mutazioni

| Hook | Operazione Supabase |
|---|---|
| `useTogglePublish(idea)` | riceve l'`Idea` completa; `UPDATE SET published = !idea.published, published_at = now()/null` |
| `useUpdateIdea(id)` | `UPDATE SET title, summary, category, tags, notes, updated_at = now()` |
| `useSoftDelete(id)` | `UPDATE SET deleted_at = now()` |
| `useRestore(id)` | `UPDATE SET deleted_at = null` |
| `useHardDelete(id)` | `DELETE WHERE id = ?` |

---

## 7. Componenti

### `App.tsx`

State locale: `tab: Tab` (default `'inbox'`), `filters: Filters`.

```
<QueryClientProvider>
  <TopBar />          ← brand + TabNav
  <FilterBar />       ← search + categoria + tag chips
  <IdeaList />        ← lista righe filtrata
  <EditModal />       ← drawer, controlled da selectedIdea
</QueryClientProvider>
```

### `TabNav.tsx`

Tre tab orizzontali. Badge numerico (count items) solo su Inbox. Click cambia tab e resetta i filtri attivi.

### `IdeaRow.tsx`

Colonne: thumbnail (36×36, emoji fallback per source_type) · titolo + meta (categoria badge + tags + timestamp relativo) · azioni.

**Azioni per tab:**

| Azione | Inbox | Published | Trash |
|---|---|---|---|
| Pubblica | ✅ | — | — |
| Annulla pubblicazione | — | ✅ | — |
| Edit (apre modal) | ✅ | ✅ | — |
| Sposta in Trash | ✅ | ✅ | — |
| Ripristina | — | — | ✅ |
| Elimina definitivamente | — | — | ✅ (confirm dialog) |

### `FilterBar.tsx`

Tre controlli in riga:
1. Input testo → debounced (300ms) → filtra su `title` + `summary`
2. Dropdown categoria (9 valori statici + "Tutte")
3. Tag chips — lista dinamica estratta dalle ideas della vista corrente, multi-select toggle

### `EditModal.tsx`

shadcn `<Sheet side="right">` — larghezza 400px. Campi:
- `title` — `<input>`
- `summary` — `<textarea>`
- `category` — `<Select>` shadcn
- `tags` — input pill custom (aggiungi con Enter, rimuovi con ×)
- `notes` — `<textarea>` (label "Note private — mai pubblicate")

Submit → `useUpdateIdea` → chiude sheet → toast conferma.

---

## 8. Visual Design

| Elemento | Valore |
|---|---|
| Font display (headings, brand) | Syne (Google Fonts) |
| Font body | DM Sans |
| Font mono (label, tag, meta) | DM Mono |
| Background | `#060608` |
| Surface | `#0e0e14` |
| Border | `#1c1c24` |
| Testo primario | `#e2e2e8` |
| Accent indigo | `#7c6af7` |
| Verde (pubblica) | `#4ade80` |
| Rosso (elimina) | `#ef4444` |

I colori categoria hanno palette dedicata (indigo → ai, blue → tech, green → crossfit, orange → food, ecc.).

---

## 9. Aggiunta al `.gitignore`

```
admin/.env.local
admin/node_modules/
admin/dist/
```

---

## Fuori scope (Phase 3)

- Deploy (è locale-only)
- Auth / magic link (non necessario in locale)
- Bulk actions (multi-select + pubblica/elimina)
- Sort order drag-and-drop (`sort_order` column esiste ma non usata)
- Anteprima rendering della card pubblica
- Frontend pubblico /discoveries (Phase 4)
- Semantic search / embeddings (Phase 5)
