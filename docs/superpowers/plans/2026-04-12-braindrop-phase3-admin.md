# BrainDrop Phase 3 — Admin Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Costruire un admin panel React+Vite locale che permette di gestire le idee BrainDrop: visualizzare Inbox/Published/Trash, filtrare per testo/categoria/tag, pubblicare/archiviare, modificare campi e cancellare.

**Architecture:** App React 19 + Vite nella cartella `admin/` del repo BrainDrop. Accede a Supabase direttamente con service_role key (nessun layer backend, nessun auth). TanStack Query v5 per server state. shadcn/ui per Sheet e Select. Dark theme con Syne + DM Sans + DM Mono.

**Tech Stack:** React 19, Vite 5, TypeScript 5, Tailwind CSS 3, shadcn/ui, @supabase/supabase-js v2, @tanstack/react-query v5, sonner (toast), vitest + @testing-library/react

---

## File Map

```
admin/
├── index.html
├── vite.config.ts               # Vite + vitest config + path alias @/
├── tailwind.config.ts
├── postcss.config.js
├── tsconfig.json
├── tsconfig.node.json
├── package.json
├── .env.local                   # VITE_SUPABASE_URL + VITE_SUPABASE_SERVICE_KEY
└── src/
    ├── main.tsx                 # QueryClientProvider + Toaster + App
    ├── App.tsx                  # tab/filter state, layout shell
    ├── index.css                # Tailwind directives, Google Fonts, CSS vars
    ├── test/
    │   └── setup.ts             # @testing-library/jest-dom setup
    ├── types.ts                 # Idea, Tab, Filters, Category, SourceType
    ├── lib/
    │   ├── supabase.ts          # createClient singleton
    │   ├── queries.ts           # useIdeas + 5 mutation hooks
    │   └── __tests__/
    │       └── queries.test.ts  # hook tests con supabase mockato
    └── components/
        ├── TabNav.tsx           # 3 tab orizzontali + badge Inbox
        ├── FilterBar.tsx        # search debounced + categoria + tag chips
        ├── IdeaRow.tsx          # riga: thumb + titolo + meta + azioni per tab
        ├── EditModal.tsx        # Sheet laterale con form editing
        └── __tests__/
            ├── TabNav.test.tsx
            ├── FilterBar.test.tsx
            ├── IdeaRow.test.tsx
            └── EditModal.test.tsx
```

---

## Task 1: Project Bootstrap

**Files:**
- Create: `admin/` (tutta la struttura)
- Modify: `.gitignore` (aggiunte admin)

- [ ] **Step 1: Crea il progetto Vite da radice del repo**

```bash
npm create vite@latest admin -- --template react-ts
```

Risposta ai prompt: nome progetto `admin`, framework `React`, variante `TypeScript`.

- [ ] **Step 2: Installa le dipendenze runtime**

```bash
cd admin
npm install @supabase/supabase-js @tanstack/react-query @tanstack/react-query-devtools sonner
```

- [ ] **Step 3: Installa le dipendenze di sviluppo**

```bash
npm install -D tailwindcss autoprefixer postcss @types/node \
  vitest @testing-library/react @testing-library/jest-dom \
  @testing-library/user-event jsdom
```

- [ ] **Step 4: Scrivi `vite.config.ts`** (sostituisce quello generato)

```ts
/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
```

- [ ] **Step 5: Scrivi `tailwind.config.ts`**

```ts
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: { extend: {} },
  plugins: [],
} satisfies Config
```

- [ ] **Step 6: Scrivi `postcss.config.js`**

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 7: Aggiorna `tsconfig.json`** (aggiungi path aliases)

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

Apri `tsconfig.app.json` (creato da Vite) e aggiungi nel `compilerOptions`:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

- [ ] **Step 8: Crea `src/test/setup.ts`**

```ts
import '@testing-library/jest-dom'
```

- [ ] **Step 9: Inizializza shadcn/ui**

```bash
npx shadcn@latest init -y
```

Quando chiede la directory dei componenti: `src/components/ui`. Se chiede il framework Tailwind: seleziona Tailwind CSS.

```bash
npx shadcn@latest add sheet select
```

- [ ] **Step 10: Aggiungi al `.gitignore` della root del repo**

Apri il `.gitignore` nella root di BrainDrop e aggiungi in fondo:

```
# Admin panel
admin/.env.local
admin/node_modules/
admin/dist/
```

- [ ] **Step 11: Verifica che il dev server parta**

```bash
npm run dev
```

Expected: `Local: http://localhost:5173/` senza errori.

- [ ] **Step 12: Commit**

```bash
cd ..
git add admin/ .gitignore
git commit -m "feat: scaffold admin panel (Vite + React + Tailwind + shadcn)"
```

---

## Task 2: Tipi

**Files:**
- Create: `admin/src/types.ts`

- [ ] **Step 1: Scrivi `src/types.ts`**

```ts
export type SourceType =
  | 'url'
  | 'text'
  | 'instagram'
  | 'photo'
  | 'voice'
  | 'youtube'

export type Category =
  | 'tech'
  | 'programming'
  | 'ai'
  | 'crossfit'
  | 'travel'
  | 'food'
  | 'business'
  | 'personal'
  | 'other'

export const CATEGORIES: Category[] = [
  'tech', 'programming', 'ai', 'crossfit',
  'travel', 'food', 'business', 'personal', 'other',
]

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

export type IdeaPatch = Partial<Pick<Idea, 'title' | 'summary' | 'category' | 'tags' | 'notes'>>

export type Tab = 'inbox' | 'published' | 'trash'

export interface Filters {
  text: string
  category: Category | ''
  tags: string[]
}

export const DEFAULT_FILTERS: Filters = { text: '', category: '', tags: [] }

export const SOURCE_TYPE_EMOJI: Record<SourceType, string> = {
  url: '🔗',
  text: '📝',
  instagram: '📸',
  photo: '🖼',
  voice: '🎙',
  youtube: '🎥',
}

export const CATEGORY_COLORS: Record<Category, { bg: string; text: string; border: string }> = {
  ai:          { bg: '#1a1a30', text: '#a89fff', border: '#2a2a50' },
  tech:        { bg: '#1a2030', text: '#60a5fa', border: '#2a3050' },
  programming: { bg: '#1a1a2a', text: '#818cf8', border: '#2a2a40' },
  crossfit:    { bg: '#1a2a1a', text: '#4ade80', border: '#2a4a2a' },
  travel:      { bg: '#2a2010', text: '#fbbf24', border: '#4a3a10' },
  food:        { bg: '#2a1a10', text: '#fb923c', border: '#4a2a10' },
  business:    { bg: '#1a2020', text: '#34d399', border: '#2a3a30' },
  personal:    { bg: '#2a1a20', text: '#f472b6', border: '#4a2a30' },
  other:       { bg: '#1a1a1a', text: '#9ca3af', border: '#2a2a2a' },
}
```

- [ ] **Step 2: Commit**

```bash
git add admin/src/types.ts
git commit -m "feat(admin): add shared types (Idea, Tab, Filters, CATEGORIES)"
```

---

## Task 3: Supabase Client

**Files:**
- Create: `admin/src/lib/supabase.ts`
- Create: `admin/.env.local`

- [ ] **Step 1: Crea `.env.local`**

```env
VITE_SUPABASE_URL=https://TUO_PROGETTO.supabase.co
VITE_SUPABASE_SERVICE_KEY=eyJ...la_tua_service_key...
```

Sostituisci con i valori reali dal dashboard Supabase → Settings → API.

- [ ] **Step 2: Scrivi `src/lib/supabase.ts`**

```ts
import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL as string
const key = import.meta.env.VITE_SUPABASE_SERVICE_KEY as string

if (!url || !key) {
  throw new Error('Missing VITE_SUPABASE_URL or VITE_SUPABASE_SERVICE_KEY in .env.local')
}

export const supabase = createClient(url, key)
```

- [ ] **Step 3: Verifica che il dev server non lanci errori**

```bash
npm run dev
```

Expected: nessun errore in console, il messaggio di errore non appare (le env vars sono presenti).

- [ ] **Step 4: Commit**

```bash
git add admin/src/lib/supabase.ts
git commit -m "feat(admin): add Supabase client singleton"
```

---

## Task 4: Query Hooks

**Files:**
- Create: `admin/src/lib/queries.ts`
- Create: `admin/src/lib/__tests__/queries.test.ts`

- [ ] **Step 1: Scrivi il test per `useIdeas`**

```ts
// src/lib/__tests__/queries.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import type { Filters } from '@/types'

// Mock del modulo supabase
const mockBuilder = {
  select: vi.fn().mockReturnThis(),
  order: vi.fn().mockReturnThis(),
  eq: vi.fn().mockReturnThis(),
  is: vi.fn().mockReturnThis(),
  not: vi.fn().mockReturnThis(),
  or: vi.fn().mockReturnThis(),
  contains: vi.fn().mockReturnThis(),
  then: vi.fn(),
}

vi.mock('@/lib/supabase', () => ({
  supabase: { from: vi.fn(() => mockBuilder) },
}))

// Helper: wrapper con QueryClient fresco per ogni test
function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children)
}

const noFilters: Filters = { text: '', category: '', tags: [] }

const mockIdea = {
  id: 'abc-123',
  title: 'Test idea',
  published: false,
  deleted_at: null,
  category: 'ai',
  tags: ['#test'],
}

describe('useIdeas', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockBuilder.then.mockImplementation((resolve: any) =>
      Promise.resolve({ data: [mockIdea], error: null }).then(resolve)
    )
  })

  it('query inbox: eq(published, false) + is(deleted_at, null)', async () => {
    const { useIdeas } = await import('@/lib/queries')
    const { result } = renderHook(() => useIdeas('inbox', noFilters), {
      wrapper: makeWrapper(),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockBuilder.eq).toHaveBeenCalledWith('published', false)
    expect(mockBuilder.is).toHaveBeenCalledWith('deleted_at', null)
  })

  it('query published: eq(published, true) + is(deleted_at, null)', async () => {
    const { useIdeas } = await import('@/lib/queries')
    const { result } = renderHook(() => useIdeas('published', noFilters), {
      wrapper: makeWrapper(),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockBuilder.eq).toHaveBeenCalledWith('published', true)
    expect(mockBuilder.is).toHaveBeenCalledWith('deleted_at', null)
  })

  it('query trash: not(deleted_at, is, null)', async () => {
    const { useIdeas } = await import('@/lib/queries')
    const { result } = renderHook(() => useIdeas('trash', noFilters), {
      wrapper: makeWrapper(),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockBuilder.not).toHaveBeenCalledWith('deleted_at', 'is', null)
  })

  it('filtro testo: chiama or() con ilike su title e summary', async () => {
    const { useIdeas } = await import('@/lib/queries')
    const { result } = renderHook(
      () => useIdeas('inbox', { ...noFilters, text: 'react' }),
      { wrapper: makeWrapper() }
    )
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockBuilder.or).toHaveBeenCalledWith(
      'title.ilike.%react%,summary.ilike.%react%'
    )
  })

  it('filtro categoria: chiama eq(category, ...)', async () => {
    const { useIdeas } = await import('@/lib/queries')
    const { result } = renderHook(
      () => useIdeas('inbox', { ...noFilters, category: 'ai' }),
      { wrapper: makeWrapper() }
    )
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockBuilder.eq).toHaveBeenCalledWith('category', 'ai')
  })

  it('filtro tags: chiama contains(tags, [...])', async () => {
    const { useIdeas } = await import('@/lib/queries')
    const { result } = renderHook(
      () => useIdeas('inbox', { ...noFilters, tags: ['llm'] }),
      { wrapper: makeWrapper() }
    )
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockBuilder.contains).toHaveBeenCalledWith('tags', ['llm'])
  })
})
```

- [ ] **Step 2: Esegui il test e verifica che fallisca**

```bash
npm run test -- src/lib/__tests__/queries.test.ts
```

Expected: FAIL — `Cannot find module '@/lib/queries'`

- [ ] **Step 3: Scrivi `src/lib/queries.ts`**

```ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { supabase } from '@/lib/supabase'
import type { Filters, Idea, IdeaPatch, Tab } from '@/types'

// ── READ ──────────────────────────────────────────────────────────────────

export function useIdeas(tab: Tab, filters: Filters) {
  return useQuery({
    queryKey: ['ideas', tab, filters],
    queryFn: async () => {
      let q = supabase.from('ideas').select('*').order('created_at', { ascending: false })

      if (tab === 'inbox')     q = q.eq('published', false).is('deleted_at', null)
      if (tab === 'published') q = q.eq('published', true).is('deleted_at', null)
      if (tab === 'trash')     q = q.not('deleted_at', 'is', null)

      if (filters.text)        q = q.or(`title.ilike.%${filters.text}%,summary.ilike.%${filters.text}%`)
      if (filters.category)    q = q.eq('category', filters.category)
      if (filters.tags.length) q = q.contains('tags', filters.tags)

      const { data, error } = await q
      if (error) throw error
      return data as Idea[]
    },
  })
}

export function useInboxCount() {
  return useQuery({
    queryKey: ['ideas', 'inbox-count'],
    queryFn: async () => {
      const { count, error } = await supabase
        .from('ideas')
        .select('*', { count: 'exact', head: true })
        .eq('published', false)
        .is('deleted_at', null)
      if (error) throw error
      return count ?? 0
    },
  })
}

// ── MUTATIONS ──────────────────────────────────────────────────────────────

export function useTogglePublish() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (idea: Idea) => {
      const now = new Date().toISOString()
      const { error } = await supabase
        .from('ideas')
        .update({
          published: !idea.published,
          published_at: idea.published ? null : now,
        })
        .eq('id', idea.id)
      if (error) throw error
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ideas'] }),
    onError: () => toast.error('Errore durante la pubblicazione'),
  })
}

export function useUpdateIdea() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, patch }: { id: string; patch: IdeaPatch }) => {
      const { error } = await supabase
        .from('ideas')
        .update({ ...patch, updated_at: new Date().toISOString() })
        .eq('id', id)
      if (error) throw error
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ideas'] })
      toast.success('Modifiche salvate')
    },
    onError: () => toast.error('Errore durante il salvataggio'),
  })
}

export function useSoftDelete() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase
        .from('ideas')
        .update({ deleted_at: new Date().toISOString() })
        .eq('id', id)
      if (error) throw error
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ideas'] }),
    onError: () => toast.error('Errore durante lo spostamento nel cestino'),
  })
}

export function useRestore() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase
        .from('ideas')
        .update({ deleted_at: null })
        .eq('id', id)
      if (error) throw error
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ideas'] }),
    onError: () => toast.error('Errore durante il ripristino'),
  })
}

export function useHardDelete() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase.from('ideas').delete().eq('id', id)
      if (error) throw error
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ideas'] })
      toast.success('Eliminata definitivamente')
    },
    onError: () => toast.error('Errore durante l\'eliminazione'),
  })
}
```

- [ ] **Step 4: Esegui il test e verifica che passi**

```bash
npm run test -- src/lib/__tests__/queries.test.ts
```

Expected: PASS (6 test)

- [ ] **Step 5: Commit**

```bash
git add admin/src/lib/queries.ts admin/src/lib/__tests__/queries.test.ts
git commit -m "feat(admin): add TanStack Query hooks for ideas CRUD"
```

---

## Task 5: App Shell + Global Styles

**Files:**
- Create/Overwrite: `admin/src/index.css`
- Create/Overwrite: `admin/src/main.tsx`
- Create/Overwrite: `admin/src/App.tsx`
- Create/Overwrite: `admin/index.html`

- [ ] **Step 1: Aggiorna `index.html` con il link ai font Google**

```html
<!doctype html>
<html lang="it">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>BrainDrop Admin</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap"
      rel="stylesheet"
    />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 2: Scrivi `src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --bg:       #060608;
  --surface:  #0e0e14;
  --surface2: #141420;
  --border:   #1c1c24;
  --border2:  #222238;
  --text:     #e2e2e8;
  --text-dim: #888;
  --text-muted: #444;
  --accent:   #7c6af7;
  --accent-bg: #2a2060;
  --green:    #4ade80;
  --green-bg: #0f2a1a;
  --red:      #ef4444;
  --red-bg:   #1a0a0a;
}

* { box-sizing: border-box; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  margin: 0;
  min-height: 100vh;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
```

- [ ] **Step 3: Scrivi `src/main.tsx`**

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from 'sonner'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster position="bottom-right" theme="dark" />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </React.StrictMode>
)
```

- [ ] **Step 4: Scrivi `src/App.tsx`** (shell con state, import componenti come placeholder per ora)

```tsx
import { useState } from 'react'
import type { Tab, Filters } from '@/types'
import { DEFAULT_FILTERS } from '@/types'
import TabNav from '@/components/TabNav'
import FilterBar from '@/components/FilterBar'
import IdeaRow from '@/components/IdeaRow'
import EditModal from '@/components/EditModal'
import { useIdeas, useInboxCount } from '@/lib/queries'
import type { Idea } from '@/types'

export default function App() {
  const [tab, setTab] = useState<Tab>('inbox')
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS)
  const [editingIdea, setEditingIdea] = useState<Idea | null>(null)

  const { data: ideas = [], isLoading } = useIdeas(tab, filters)
  const { data: inboxCount = 0 } = useInboxCount()

  function handleTabChange(newTab: Tab) {
    setTab(newTab)
    setFilters(DEFAULT_FILTERS)
  }

  // Raccoglie i tag unici dalle idee della vista corrente per i chip filtro
  const availableTags = [...new Set(ideas.flatMap((i) => i.tags))].sort()

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {/* TOP BAR */}
      <div
        style={{
          background: 'var(--surface)',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'stretch',
          height: 52,
          paddingLeft: 24,
        }}
      >
        <div
          style={{
            fontFamily: 'Syne, sans-serif',
            fontWeight: 800,
            fontSize: 13,
            letterSpacing: 3,
            textTransform: 'uppercase',
            color: 'var(--text)',
            display: 'flex',
            alignItems: 'center',
            marginRight: 32,
          }}
        >
          BrainDrop
        </div>
        <TabNav
          activeTab={tab}
          inboxCount={inboxCount}
          onTabChange={handleTabChange}
        />
      </div>

      {/* FILTER BAR */}
      <FilterBar
        filters={filters}
        availableTags={availableTags}
        onChange={setFilters}
      />

      {/* IDEA LIST */}
      <div style={{ padding: '12px 16px' }}>
        {isLoading && (
          <p style={{ color: 'var(--text-muted)', fontFamily: 'DM Mono', fontSize: 12, padding: '24px 10px' }}>
            Caricamento…
          </p>
        )}
        {!isLoading && ideas.length === 0 && (
          <p style={{ color: 'var(--text-muted)', fontFamily: 'DM Mono', fontSize: 12, padding: '24px 10px' }}>
            Nessuna idea in questa vista.
          </p>
        )}
        {ideas.map((idea) => (
          <IdeaRow
            key={idea.id}
            idea={idea}
            tab={tab}
            onEdit={() => setEditingIdea(idea)}
          />
        ))}
      </div>

      {/* EDIT MODAL */}
      <EditModal
        idea={editingIdea}
        onClose={() => setEditingIdea(null)}
      />
    </div>
  )
}
```

- [ ] **Step 5: Verifica build TypeScript senza errori**

```bash
npm run build 2>&1 | head -30
```

Expected: errori solo per moduli non ancora creati (TabNav, FilterBar, IdeaRow, EditModal). Non errori di sintassi.

- [ ] **Step 6: Commit**

```bash
git add admin/index.html admin/src/index.css admin/src/main.tsx admin/src/App.tsx
git commit -m "feat(admin): app shell with tab/filter state management"
```

---

## Task 6: TabNav

**Files:**
- Create: `admin/src/components/TabNav.tsx`
- Create: `admin/src/components/__tests__/TabNav.test.tsx`

- [ ] **Step 1: Scrivi il test**

```tsx
// src/components/__tests__/TabNav.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TabNav from '@/components/TabNav'

describe('TabNav', () => {
  it('mostra 3 tab: Inbox, Published, Trash', () => {
    render(<TabNav activeTab="inbox" inboxCount={0} onTabChange={vi.fn()} />)
    expect(screen.getByText('Inbox')).toBeInTheDocument()
    expect(screen.getByText('Published')).toBeInTheDocument()
    expect(screen.getByText('Trash')).toBeInTheDocument()
  })

  it('mostra il badge numerico solo su Inbox quando > 0', () => {
    render(<TabNav activeTab="inbox" inboxCount={7} onTabChange={vi.fn()} />)
    expect(screen.getByText('7')).toBeInTheDocument()
  })

  it('non mostra il badge se inboxCount è 0', () => {
    render(<TabNav activeTab="inbox" inboxCount={0} onTabChange={vi.fn()} />)
    expect(screen.queryByTestId('inbox-badge')).not.toBeInTheDocument()
  })

  it('chiama onTabChange con il tab corretto al click', async () => {
    const onChange = vi.fn()
    render(<TabNav activeTab="inbox" inboxCount={0} onTabChange={onChange} />)
    await userEvent.click(screen.getByText('Published'))
    expect(onChange).toHaveBeenCalledWith('published')
  })

  it('applica stile attivo al tab selezionato', () => {
    render(<TabNav activeTab="published" inboxCount={0} onTabChange={vi.fn()} />)
    const publishedTab = screen.getByText('Published').closest('[data-tab]')
    expect(publishedTab).toHaveAttribute('data-active', 'true')
  })
})
```

- [ ] **Step 2: Esegui il test e verifica che fallisca**

```bash
npm run test -- src/components/__tests__/TabNav.test.tsx
```

Expected: FAIL — `Cannot find module '@/components/TabNav'`

- [ ] **Step 3: Scrivi `src/components/TabNav.tsx`**

```tsx
import type { Tab } from '@/types'

interface Props {
  activeTab: Tab
  inboxCount: number
  onTabChange: (tab: Tab) => void
}

const tabs: { id: Tab; label: string }[] = [
  { id: 'inbox', label: 'Inbox' },
  { id: 'published', label: 'Published' },
  { id: 'trash', label: 'Trash' },
]

export default function TabNav({ activeTab, inboxCount, onTabChange }: Props) {
  return (
    <div style={{ display: 'flex', alignItems: 'stretch', flex: 1 }}>
      {tabs.map((t) => {
        const isActive = t.id === activeTab
        return (
          <button
            key={t.id}
            data-tab={t.id}
            data-active={isActive}
            onClick={() => onTabChange(t.id)}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: isActive ? '2px solid var(--accent)' : '2px solid transparent',
              color: isActive ? 'var(--text)' : 'var(--text-muted)',
              fontFamily: 'DM Sans, sans-serif',
              fontSize: 12,
              fontWeight: 500,
              letterSpacing: '0.3px',
              padding: '0 18px',
              display: 'flex',
              alignItems: 'center',
              gap: 7,
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            {t.label}
            {t.id === 'inbox' && inboxCount > 0 && (
              <span
                data-testid="inbox-badge"
                style={{
                  background: 'var(--accent)',
                  color: '#fff',
                  fontFamily: 'DM Mono, monospace',
                  fontSize: 9,
                  fontWeight: 500,
                  padding: '1px 6px',
                  borderRadius: 20,
                  letterSpacing: '0.5px',
                }}
              >
                {inboxCount}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
```

- [ ] **Step 4: Esegui il test e verifica che passi**

```bash
npm run test -- src/components/__tests__/TabNav.test.tsx
```

Expected: PASS (5 test)

- [ ] **Step 5: Commit**

```bash
git add admin/src/components/TabNav.tsx admin/src/components/__tests__/TabNav.test.tsx
git commit -m "feat(admin): TabNav component with badge and active state"
```

---

## Task 7: FilterBar

**Files:**
- Create: `admin/src/components/FilterBar.tsx`
- Create: `admin/src/components/__tests__/FilterBar.test.tsx`

- [ ] **Step 1: Scrivi il test**

```tsx
// src/components/__tests__/FilterBar.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FilterBar from '@/components/FilterBar'
import { DEFAULT_FILTERS } from '@/types'

describe('FilterBar', () => {
  it('mostra input di testo, dropdown categoria, e tag chips', () => {
    render(
      <FilterBar
        filters={DEFAULT_FILTERS}
        availableTags={['llm', 'python']}
        onChange={vi.fn()}
      />
    )
    expect(screen.getByPlaceholderText(/cerca/i)).toBeInTheDocument()
    expect(screen.getByRole('combobox')).toBeInTheDocument()
    expect(screen.getByText('#llm')).toBeInTheDocument()
    expect(screen.getByText('#python')).toBeInTheDocument()
  })

  it('chiama onChange con il testo dopo il debounce (300ms)', async () => {
    vi.useFakeTimers()
    const onChange = vi.fn()
    render(
      <FilterBar
        filters={DEFAULT_FILTERS}
        availableTags={[]}
        onChange={onChange}
      />
    )
    await userEvent.type(screen.getByPlaceholderText(/cerca/i), 'react')
    expect(onChange).not.toHaveBeenCalled()
    act(() => { vi.advanceTimersByTime(300) })
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ text: 'react' }))
    vi.useRealTimers()
  })

  it('click su tag chip attiva/disattiva il tag nei filtri', async () => {
    const onChange = vi.fn()
    render(
      <FilterBar
        filters={DEFAULT_FILTERS}
        availableTags={['llm']}
        onChange={onChange}
      />
    )
    await userEvent.click(screen.getByText('#llm'))
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ tags: ['llm'] }))
  })

  it('click su tag già attivo lo rimuove dai filtri', async () => {
    const onChange = vi.fn()
    render(
      <FilterBar
        filters={{ ...DEFAULT_FILTERS, tags: ['llm'] }}
        availableTags={['llm']}
        onChange={onChange}
      />
    )
    await userEvent.click(screen.getByText('#llm'))
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ tags: [] }))
  })
})
```

- [ ] **Step 2: Esegui il test e verifica che fallisca**

```bash
npm run test -- src/components/__tests__/FilterBar.test.tsx
```

Expected: FAIL

- [ ] **Step 3: Scrivi `src/components/FilterBar.tsx`**

```tsx
import { useEffect, useRef, useState } from 'react'
import type { Category, Filters } from '@/types'
import { CATEGORIES } from '@/types'

interface Props {
  filters: Filters
  availableTags: string[]
  onChange: (filters: Filters) => void
}

export default function FilterBar({ filters, availableTags, onChange }: Props) {
  const [inputValue, setInputValue] = useState(filters.text)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Sync local input when filters reset externally (tab change)
  useEffect(() => { setInputValue(filters.text) }, [filters.text])

  function handleTextChange(value: string) {
    setInputValue(value)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      onChange({ ...filters, text: value })
    }, 300)
  }

  function handleCategoryChange(category: Category | '') {
    onChange({ ...filters, category })
  }

  function toggleTag(tag: string) {
    const next = filters.tags.includes(tag)
      ? filters.tags.filter((t) => t !== tag)
      : [...filters.tags, tag]
    onChange({ ...filters, tags: next })
  }

  return (
    <div
      style={{
        background: 'var(--surface)',
        borderBottom: '1px solid #1a1a22',
        padding: '10px 24px',
        display: 'flex',
        gap: 10,
        alignItems: 'center',
        flexWrap: 'wrap',
      }}
    >
      <input
        type="text"
        placeholder="Cerca per titolo o summary…"
        value={inputValue}
        onChange={(e) => handleTextChange(e.target.value)}
        style={{
          background: 'var(--surface2)',
          border: '1px solid var(--border2)',
          borderRadius: 6,
          padding: '6px 12px',
          color: '#aaa',
          fontFamily: 'DM Sans, sans-serif',
          fontSize: 12,
          width: 220,
          outline: 'none',
        }}
      />

      <select
        value={filters.category}
        onChange={(e) => handleCategoryChange(e.target.value as Category | '')}
        style={{
          background: 'var(--surface2)',
          border: '1px solid var(--border2)',
          borderRadius: 6,
          padding: '6px 10px',
          color: filters.category ? 'var(--text)' : 'var(--text-muted)',
          fontFamily: 'DM Mono, monospace',
          fontSize: 11,
          outline: 'none',
          cursor: 'pointer',
        }}
      >
        <option value="">Categoria</option>
        {CATEGORIES.map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>

      {availableTags.map((tag) => {
        const isActive = filters.tags.includes(tag)
        return (
          <button
            key={tag}
            onClick={() => toggleTag(tag)}
            style={{
              background: isActive ? 'var(--accent-bg)' : 'var(--surface2)',
              border: `1px solid ${isActive ? 'var(--accent)' : 'var(--border2)'}`,
              borderRadius: 20,
              padding: '3px 10px',
              fontFamily: 'DM Mono, monospace',
              fontSize: 10,
              color: isActive ? '#a89fff' : 'var(--text-muted)',
              cursor: 'pointer',
              transition: 'all 0.12s',
            }}
          >
            #{tag}
          </button>
        )
      })}
    </div>
  )
}
```

- [ ] **Step 4: Esegui il test e verifica che passi**

```bash
npm run test -- src/components/__tests__/FilterBar.test.tsx
```

Expected: PASS (4 test)

- [ ] **Step 5: Commit**

```bash
git add admin/src/components/FilterBar.tsx admin/src/components/__tests__/FilterBar.test.tsx
git commit -m "feat(admin): FilterBar with debounced search, category, tag chips"
```

---

## Task 8: IdeaRow

**Files:**
- Create: `admin/src/components/IdeaRow.tsx`
- Create: `admin/src/components/__tests__/IdeaRow.test.tsx`

- [ ] **Step 1: Scrivi il test**

```tsx
// src/components/__tests__/IdeaRow.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import IdeaRow from '@/components/IdeaRow'
import type { Idea } from '@/types'

// Mock delle mutation hooks (non testiamo il DB qui)
vi.mock('@/lib/queries', () => ({
  useTogglePublish: () => ({ mutate: vi.fn(), isPending: false }),
  useSoftDelete: () => ({ mutate: vi.fn(), isPending: false }),
  useRestore: () => ({ mutate: vi.fn(), isPending: false }),
  useHardDelete: () => ({ mutate: vi.fn(), isPending: false }),
}))

const baseIdea: Idea = {
  id: 'abc-1',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  title: 'Test idea title',
  summary: 'A summary',
  original_content: 'raw',
  enrichment_data: {},
  source_type: 'url',
  category: 'ai',
  tags: ['llm', 'test'],
  media_url: null,
  source_url: null,
  thumbnail_url: null,
  published: false,
  published_at: null,
  deleted_at: null,
  notes: null,
  sort_order: 0,
}

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient()
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

describe('IdeaRow', () => {
  it('mostra il titolo dell\'idea', () => {
    wrap(<IdeaRow idea={baseIdea} tab="inbox" onEdit={vi.fn()} />)
    expect(screen.getByText('Test idea title')).toBeInTheDocument()
  })

  it('Inbox: mostra "Pubblica", "Edit", "Cestina"', () => {
    wrap(<IdeaRow idea={baseIdea} tab="inbox" onEdit={vi.fn()} />)
    expect(screen.getByText('Pubblica')).toBeInTheDocument()
    expect(screen.getByText('Edit')).toBeInTheDocument()
    expect(screen.getByTitle('Sposta nel cestino')).toBeInTheDocument()
    expect(screen.queryByText('Ripristina')).not.toBeInTheDocument()
  })

  it('Published: mostra "Annulla" invece di "Pubblica"', () => {
    const published = { ...baseIdea, published: true, published_at: new Date().toISOString() }
    wrap(<IdeaRow idea={published} tab="published" onEdit={vi.fn()} />)
    expect(screen.getByText('Annulla')).toBeInTheDocument()
    expect(screen.queryByText('Pubblica')).not.toBeInTheDocument()
  })

  it('Trash: mostra "Ripristina" e "Elimina"', () => {
    const trashed = { ...baseIdea, deleted_at: new Date().toISOString() }
    wrap(<IdeaRow idea={trashed} tab="trash" onEdit={vi.fn()} />)
    expect(screen.getByText('Ripristina')).toBeInTheDocument()
    expect(screen.getByText('Elimina')).toBeInTheDocument()
    expect(screen.queryByText('Pubblica')).not.toBeInTheDocument()
    expect(screen.queryByText('Edit')).not.toBeInTheDocument()
  })

  it('click su Edit chiama onEdit', async () => {
    const onEdit = vi.fn()
    wrap(<IdeaRow idea={baseIdea} tab="inbox" onEdit={onEdit} />)
    await userEvent.click(screen.getByText('Edit'))
    expect(onEdit).toHaveBeenCalledTimes(1)
  })
})
```

- [ ] **Step 2: Esegui il test e verifica che fallisca**

```bash
npm run test -- src/components/__tests__/IdeaRow.test.tsx
```

Expected: FAIL

- [ ] **Step 3: Scrivi `src/components/IdeaRow.tsx`**

```tsx
import type { CSSProperties } from 'react'
import type { Idea, Tab } from '@/types'
import { SOURCE_TYPE_EMOJI, CATEGORY_COLORS } from '@/types'
import { useTogglePublish, useSoftDelete, useRestore, useHardDelete } from '@/lib/queries'

interface Props {
  idea: Idea
  tab: Tab
  onEdit: () => void
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 60) return `${mins}m fa`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h fa`
  const days = Math.floor(hours / 24)
  if (days === 1) return 'ieri'
  return `${days}g fa`
}

export default function IdeaRow({ idea, tab, onEdit }: Props) {
  const togglePublish = useTogglePublish()
  const softDelete = useSoftDelete()
  const restore = useRestore()
  const hardDelete = useHardDelete()

  const catColors = CATEGORY_COLORS[idea.category] ?? CATEGORY_COLORS.other

  function confirmHardDelete() {
    if (window.confirm(`Eliminare definitivamente "${idea.title}"? Questa azione è irreversibile.`)) {
      hardDelete.mutate(idea.id)
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '10px 10px',
        borderRadius: 8,
        border: '1px solid transparent',
        marginBottom: 4,
        transition: 'all 0.12s',
      }}
      onMouseEnter={(e) => {
        const el = e.currentTarget as HTMLElement
        el.style.background = '#111118'
        el.style.borderColor = '#1e1e2c'
      }}
      onMouseLeave={(e) => {
        const el = e.currentTarget as HTMLElement
        el.style.background = 'transparent'
        el.style.borderColor = 'transparent'
      }}
    >
      {/* THUMBNAIL */}
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: 6,
          background: '#1a1a26',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 16,
          border: '1px solid #222230',
          overflow: 'hidden',
        }}
      >
        {idea.thumbnail_url ? (
          <img
            src={idea.thumbnail_url}
            alt=""
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            onError={(e) => {
              const el = e.currentTarget as HTMLImageElement
              el.style.display = 'none'
              el.parentElement!.textContent = SOURCE_TYPE_EMOJI[idea.source_type]
            }}
          />
        ) : (
          SOURCE_TYPE_EMOJI[idea.source_type]
        )}
      </div>

      {/* MAIN INFO */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontFamily: 'DM Sans, sans-serif',
            fontSize: 13,
            fontWeight: 500,
            color: '#dddde8',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            marginBottom: 4,
          }}
        >
          {idea.title}
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
          <span
            style={{
              fontFamily: 'DM Mono, monospace',
              fontSize: 9,
              letterSpacing: 1,
              textTransform: 'uppercase',
              padding: '2px 7px',
              borderRadius: 4,
              background: catColors.bg,
              color: catColors.text,
              border: `1px solid ${catColors.border}`,
            }}
          >
            {idea.category}
          </span>
          {idea.tags.length > 0 && (
            <span style={{ fontFamily: 'DM Mono, monospace', fontSize: 10, color: '#3a3a50' }}>
              {idea.tags.map((t) => `#${t}`).join(' · ')}
            </span>
          )}
        </div>
      </div>

      {/* TIME */}
      <div
        style={{
          fontFamily: 'DM Mono, monospace',
          fontSize: 10,
          color: '#2e2e42',
          flexShrink: 0,
        }}
      >
        {timeAgo(idea.created_at)}
      </div>

      {/* ACTIONS */}
      <div style={{ display: 'flex', gap: 4, alignItems: 'center', flexShrink: 0 }}>
        {/* Inbox */}
        {tab === 'inbox' && (
          <button
            onClick={() => togglePublish.mutate(idea)}
            disabled={togglePublish.isPending}
            style={btnStyle('green')}
          >
            Pubblica
          </button>
        )}

        {/* Published */}
        {tab === 'published' && (
          <button
            onClick={() => togglePublish.mutate(idea)}
            disabled={togglePublish.isPending}
            style={btnStyle('dim')}
          >
            Annulla
          </button>
        )}

        {/* Edit — Inbox + Published */}
        {(tab === 'inbox' || tab === 'published') && (
          <button onClick={onEdit} style={btnStyle('edit')}>
            Edit
          </button>
        )}

        {/* Soft delete — Inbox + Published */}
        {(tab === 'inbox' || tab === 'published') && (
          <button
            onClick={() => softDelete.mutate(idea.id)}
            disabled={softDelete.isPending}
            title="Sposta nel cestino"
            style={btnStyle('trash')}
          >
            🗑
          </button>
        )}

        {/* Trash actions */}
        {tab === 'trash' && (
          <>
            <button
              onClick={() => restore.mutate(idea.id)}
              disabled={restore.isPending}
              style={btnStyle('dim')}
            >
              Ripristina
            </button>
            <button
              onClick={confirmHardDelete}
              disabled={hardDelete.isPending}
              style={btnStyle('red')}
            >
              Elimina
            </button>
          </>
        )}
      </div>
    </div>
  )
}

function btnStyle(variant: 'green' | 'dim' | 'edit' | 'trash' | 'red'): CSSProperties {
  const base: React.CSSProperties = {
    fontFamily: 'DM Mono, monospace',
    fontSize: 10,
    letterSpacing: '0.5px',
    padding: '4px 10px',
    borderRadius: 5,
    border: 'none',
    cursor: 'pointer',
    transition: 'all 0.12s',
  }
  const styles: Record<typeof variant, CSSProperties> = {
    green: { ...base, background: '#0f2a1a', color: '#4ade80', border: '1px solid #1a4a2a' },
    dim:   { ...base, background: '#16162a', color: '#888',    border: '1px solid #222238' },
    edit:  { ...base, background: '#16162a', color: '#888',    border: '1px solid #222238' },
    trash: { ...base, background: 'transparent', color: '#444', border: '1px solid transparent', padding: '4px 6px' },
    red:   { ...base, background: '#1a0a0a', color: '#ef4444', border: '1px solid #3a1a1a' },
  }
  return styles[variant]
}
```

- [ ] **Step 4: Esegui il test e verifica che passi**

```bash
npm run test -- src/components/__tests__/IdeaRow.test.tsx
```

Expected: PASS (5 test)

- [ ] **Step 5: Commit**

```bash
git add admin/src/components/IdeaRow.tsx admin/src/components/__tests__/IdeaRow.test.tsx
git commit -m "feat(admin): IdeaRow with per-tab actions (publish, edit, delete, restore)"
```

---

## Task 9: EditModal

**Files:**
- Create: `admin/src/components/EditModal.tsx`
- Create: `admin/src/components/__tests__/EditModal.test.tsx`

- [ ] **Step 1: Scrivi il test**

```tsx
// src/components/__tests__/EditModal.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import EditModal from '@/components/EditModal'
import type { Idea } from '@/types'

const mockUpdateMutate = vi.fn()

vi.mock('@/lib/queries', () => ({
  useUpdateIdea: () => ({ mutate: mockUpdateMutate, isPending: false }),
}))

const idea: Idea = {
  id: 'abc-1',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  title: 'Titolo di test',
  summary: 'Summary di test',
  original_content: 'raw',
  enrichment_data: {},
  source_type: 'url',
  category: 'ai',
  tags: ['llm', 'test'],
  media_url: null,
  source_url: null,
  thumbnail_url: null,
  published: false,
  published_at: null,
  deleted_at: null,
  notes: 'nota privata',
  sort_order: 0,
}

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient()
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

describe('EditModal', () => {
  it('non renderizza nulla se idea è null', () => {
    const { container } = wrap(<EditModal idea={null} onClose={vi.fn()} />)
    expect(container.firstChild).toBeNull()
  })

  it('mostra il titolo attuale nell\'input', () => {
    wrap(<EditModal idea={idea} onClose={vi.fn()} />)
    expect(screen.getByDisplayValue('Titolo di test')).toBeInTheDocument()
  })

  it('mostra il summary attuale nella textarea', () => {
    wrap(<EditModal idea={idea} onClose={vi.fn()} />)
    expect(screen.getByDisplayValue('Summary di test')).toBeInTheDocument()
  })

  it('mostra i tag esistenti come pill', () => {
    wrap(<EditModal idea={idea} onClose={vi.fn()} />)
    expect(screen.getByText('#llm')).toBeInTheDocument()
    expect(screen.getByText('#test')).toBeInTheDocument()
  })

  it('click su Annulla chiama onClose', async () => {
    const onClose = vi.fn()
    wrap(<EditModal idea={idea} onClose={onClose} />)
    await userEvent.click(screen.getByText('Annulla'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('click su Salva chiama useUpdateIdea con patch corretta', async () => {
    const onClose = vi.fn()
    wrap(<EditModal idea={idea} onClose={onClose} />)
    await userEvent.click(screen.getByText('Salva'))
    expect(mockUpdateMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'abc-1',
        patch: expect.objectContaining({ title: 'Titolo di test', category: 'ai' }),
      }),
      expect.any(Object)
    )
  })
})
```

- [ ] **Step 2: Esegui il test e verifica che fallisca**

```bash
npm run test -- src/components/__tests__/EditModal.test.tsx
```

Expected: FAIL

- [ ] **Step 3: Scrivi `src/components/EditModal.tsx`**

```tsx
import { useEffect, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import type { Category, Idea, IdeaPatch } from '@/types'
import { CATEGORIES } from '@/types'
import { useUpdateIdea } from '@/lib/queries'

interface Props {
  idea: Idea | null
  onClose: () => void
}

export default function EditModal({ idea, onClose }: Props) {
  const updateIdea = useUpdateIdea()

  const [title, setTitle] = useState('')
  const [summary, setSummary] = useState('')
  const [category, setCategory] = useState<Category>('other')
  const [tags, setTags] = useState<string[]>([])
  const [notes, setNotes] = useState('')
  const [tagInput, setTagInput] = useState('')

  // Popola il form quando cambia l'idea selezionata
  useEffect(() => {
    if (idea) {
      setTitle(idea.title)
      setSummary(idea.summary)
      setCategory(idea.category)
      setTags(idea.tags)
      setNotes(idea.notes ?? '')
    }
  }, [idea])

  if (!idea) return null

  function handleTagKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault()
      const newTag = tagInput.trim().replace(/^#+/, '')
      if (!tags.includes(newTag)) setTags([...tags, newTag])
      setTagInput('')
    }
  }

  function removeTag(tag: string) {
    setTags(tags.filter((t) => t !== tag))
  }

  function handleSave() {
    const patch: IdeaPatch = { title, summary, category, tags, notes: notes || null }
    updateIdea.mutate(
      { id: idea.id, patch },
      { onSuccess: onClose }
    )
  }

  return (
    <Sheet open={!!idea} onOpenChange={(open) => { if (!open) onClose() }}>
      <SheetContent
        side="right"
        style={{
          width: 400,
          background: 'var(--surface)',
          border: 'none',
          borderLeft: '1px solid var(--border)',
          padding: '28px 24px',
          display: 'flex',
          flexDirection: 'column',
          gap: 20,
          boxShadow: '-20px 0 60px rgba(0,0,0,0.5)',
        }}
      >
        <SheetHeader>
          <SheetTitle
            style={{
              fontFamily: 'Syne, sans-serif',
              fontSize: 14,
              fontWeight: 700,
              letterSpacing: 2,
              textTransform: 'uppercase',
              color: 'var(--text)',
            }}
          >
            Edit idea
          </SheetTitle>
        </SheetHeader>

        {/* TITOLO */}
        <FieldGroup label="Titolo">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            style={inputStyle}
          />
        </FieldGroup>

        {/* SUMMARY */}
        <FieldGroup label="Summary">
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            style={{ ...inputStyle, minHeight: 80, resize: 'vertical', lineHeight: 1.5 }}
          />
        </FieldGroup>

        {/* CATEGORIA */}
        <FieldGroup label="Categoria">
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as Category)}
            style={inputStyle}
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </FieldGroup>

        {/* TAGS */}
        <FieldGroup label="Tags">
          <div
            style={{
              display: 'flex',
              gap: 5,
              flexWrap: 'wrap',
              background: 'var(--surface2)',
              border: '1px solid var(--border2)',
              borderRadius: 6,
              padding: '6px 10px',
              minHeight: 38,
              alignItems: 'center',
            }}
          >
            {tags.map((tag) => (
              <span
                key={tag}
                style={{
                  background: 'var(--accent-bg)',
                  color: '#a89fff',
                  border: '1px solid #3a3080',
                  borderRadius: 20,
                  padding: '2px 8px',
                  fontFamily: 'DM Mono, monospace',
                  fontSize: 10,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                }}
              >
                #{tag}
                <span
                  onClick={() => removeTag(tag)}
                  style={{ color: 'var(--accent)', cursor: 'pointer' }}
                >
                  ×
                </span>
              </span>
            ))}
            <input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={handleTagKeyDown}
              placeholder="+ tag"
              style={{
                background: 'none',
                border: 'none',
                outline: 'none',
                color: '#666',
                fontFamily: 'DM Mono, monospace',
                fontSize: 11,
                width: 80,
              }}
            />
          </div>
        </FieldGroup>

        {/* NOTE PRIVATE */}
        <FieldGroup label="Note private — mai pubblicate">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Note personali…"
            style={{ ...inputStyle, minHeight: 64, resize: 'vertical', lineHeight: 1.5, color: notes ? 'var(--text)' : undefined, fontStyle: notes ? 'normal' : 'italic' }}
          />
        </FieldGroup>

        {/* FOOTER */}
        <div
          style={{
            display: 'flex',
            gap: 8,
            justifyContent: 'flex-end',
            marginTop: 'auto',
            paddingTop: 12,
            borderTop: '1px solid #1a1a28',
          }}
        >
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: '1px solid var(--border2)',
              color: '#555',
              fontFamily: 'DM Mono, monospace',
              fontSize: 11,
              padding: '7px 16px',
              borderRadius: 6,
              cursor: 'pointer',
            }}
          >
            Annulla
          </button>
          <button
            onClick={handleSave}
            disabled={updateIdea.isPending}
            style={{
              background: 'var(--accent)',
              border: 'none',
              color: '#fff',
              fontFamily: 'DM Mono, monospace',
              fontSize: 11,
              fontWeight: 500,
              padding: '7px 20px',
              borderRadius: 6,
              cursor: 'pointer',
              letterSpacing: '0.5px',
              opacity: updateIdea.isPending ? 0.7 : 1,
            }}
          >
            Salva
          </button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

function FieldGroup({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div
        style={{
          fontFamily: 'DM Mono, monospace',
          fontSize: 10,
          letterSpacing: '1.5px',
          textTransform: 'uppercase',
          color: 'var(--text-muted)',
        }}
      >
        {label}
      </div>
      {children}
    </div>
  )
}

const inputStyle: CSSProperties = {
  background: 'var(--surface2)',
  border: '1px solid var(--border2)',
  borderRadius: 6,
  padding: '8px 12px',
  color: 'var(--text)',
  fontFamily: 'DM Sans, sans-serif',
  fontSize: 13,
  outline: 'none',
  width: '100%',
}
```

- [ ] **Step 4: Esegui il test e verifica che passi**

```bash
npm run test -- src/components/__tests__/EditModal.test.tsx
```

Expected: PASS (6 test)

- [ ] **Step 5: Verifica visivamente il dev server**

```bash
npm run dev
```

Apri http://localhost:5173 — la app deve caricarsi, mostrare i tab, la filter bar, le idee da Supabase, e aprire il modal cliccando "Edit".

- [ ] **Step 6: Esegui tutti i test**

```bash
npm run test
```

Expected: PASS (tutti i test — queries + TabNav + FilterBar + IdeaRow + EditModal)

- [ ] **Step 7: Commit finale**

```bash
git add admin/src/components/EditModal.tsx admin/src/components/__tests__/EditModal.test.tsx
git commit -m "feat(admin): EditModal with sheet, tag pills, save/cancel"
```

---

## Task 10: Pulizia Finale

**Files:**
- Delete: `admin/src/App.css` (generato da Vite, non usato)
- Delete: `admin/src/assets/react.svg` (non usato)

- [ ] **Step 1: Rimuovi file non utilizzati**

```bash
cd admin
rm src/App.css src/assets/react.svg
```

- [ ] **Step 2: Verifica nessun errore TypeScript**

```bash
npm run build 2>&1
```

Expected: `✓ built in ...ms` senza errori.

- [ ] **Step 3: Verifica tutti i test passano**

```bash
npm run test -- --run
```

Expected: tutti PASS.

- [ ] **Step 4: Commit finale**

```bash
git add -A
git commit -m "feat(admin): Phase 3 admin panel complete — inbox/published/trash + edit modal"
```
