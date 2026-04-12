import { useState, useEffect } from 'react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'
import { LoginPage } from '@/components/LoginPage'
import TabNav from '@/components/TabNav'
import FilterBar from '@/components/FilterBar'
import IdeaRow from '@/components/IdeaRow'
import EditModal from '@/components/EditModal'
import { useIdeas, useInboxCount } from '@/lib/queries'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import type { Tab, Filters, Idea } from '@/types'
import { DEFAULT_FILTERS } from '@/types'

function AdminShell() {
  const [tab, setTab] = useState<Tab>('inbox')
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS)
  const [editingIdea, setEditingIdea] = useState<Idea | null>(null)

  const qc = useQueryClient()
  const { data: ideas = [], isLoading } = useIdeas(tab, filters)
  const { data: inboxCount = 0 } = useInboxCount()

  async function handleClearAll() {
    if (!window.confirm('Eliminare TUTTE le idee? Operazione irreversibile.')) return
    const { error } = await supabase.from('ideas').delete().neq('id', '00000000-0000-0000-0000-000000000000')
    if (error) {
      toast.error('Errore durante la cancellazione')
    } else {
      qc.invalidateQueries({ queryKey: ['ideas'] })
      toast.success('Database svuotato')
    }
  }

  function handleTabChange(newTab: Tab) {
    setTab(newTab)
    setFilters(DEFAULT_FILTERS)
  }

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
            fontFamily: 'var(--font-display)',
            fontWeight: 800,
            fontSize: 14,
            letterSpacing: 3,
            textTransform: 'uppercase',
            color: 'var(--fg)',
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
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, paddingRight: 16 }}>
          <button
            onClick={handleClearAll}
            style={{
              background: 'none',
              border: '1px solid var(--red)',
              borderRadius: 4,
              color: 'var(--red)',
              fontSize: 12,
              padding: '4px 10px',
              cursor: 'pointer',
              fontFamily: 'var(--font-body)',
            }}
          >
            Svuota DB
          </button>
          <button
            onClick={() => supabase.auth.signOut()}
            style={{
              background: 'none',
              border: '1px solid var(--border)',
              borderRadius: 4,
              color: 'var(--fg-muted)',
              fontSize: 12,
              padding: '4px 10px',
              cursor: 'pointer',
              fontFamily: 'var(--font-body)',
            }}
          >
            Esci
          </button>
        </div>
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
          <p style={{ color: 'var(--fg-dim)', fontFamily: 'var(--font-mono)', fontSize: 13, padding: '24px 10px' }}>
            Caricamento…
          </p>
        )}
        {!isLoading && ideas.length === 0 && (
          <p style={{ color: 'var(--fg-dim)', fontFamily: 'var(--font-mono)', fontSize: 13, padding: '24px 10px' }}>
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

export default function App() {
  const [session, setSession] = useState<Session | null | undefined>(undefined)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session))
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })
    return () => subscription.unsubscribe()
  }, [])

  // Still loading auth state
  if (session === undefined) return null

  if (!session) return <LoginPage />

  return <AdminShell />
}
