import { useState } from 'react'
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
  const [notesOpen, setNotesOpen] = useState(false)

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
        borderRadius: 8,
        border: '1px solid transparent',
        marginBottom: 2,
        transition: 'border-color 0.12s, background 0.12s',
      }}
      onMouseEnter={(e) => {
        const el = e.currentTarget as HTMLElement
        el.style.background = 'var(--surface)'
        el.style.borderColor = 'var(--border)'
      }}
      onMouseLeave={(e) => {
        const el = e.currentTarget as HTMLElement
        el.style.background = 'transparent'
        el.style.borderColor = 'transparent'
      }}
    >
      {/* MAIN ROW */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '11px 12px' }}>

        {/* THUMBNAIL */}
        <div
          style={{
            width: 38,
            height: 38,
            borderRadius: 8,
            background: 'var(--surface2)',
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 17,
            border: '1px solid var(--border)',
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
              fontFamily: 'var(--font-body)',
              fontSize: 14,
              fontWeight: 500,
              color: 'var(--fg)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              marginBottom: 5,
            }}
          >
            {idea.title}
          </div>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                letterSpacing: '0.8px',
                textTransform: 'uppercase',
                padding: '2px 8px',
                borderRadius: 4,
                background: catColors.bg,
                color: catColors.text,
                border: `1px solid ${catColors.border}`,
                fontWeight: 500,
              }}
            >
              {idea.category}
            </span>
            {idea.tags.length > 0 && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-dim)' }}>
                {idea.tags.map((t) => `#${t}`).join(' · ')}
              </span>
            )}
          </div>
        </div>

        {/* SOURCE LINK */}
        {idea.source_url && (
          <a
            href={idea.source_url}
            target="_blank"
            rel="noopener noreferrer"
            title={idea.source_url}
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'transparent',
              border: '1px solid var(--border2)',
              borderRadius: 5,
              padding: '4px 8px',
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              color: 'var(--fg-muted)',
              cursor: 'pointer',
              textDecoration: 'none',
              flexShrink: 0,
              transition: 'all 0.12s',
              lineHeight: 1,
            }}
            onMouseEnter={(e) => {
              const el = e.currentTarget as HTMLAnchorElement
              el.style.borderColor = '#93c5fd'
              el.style.color = '#3b82f6'
              el.style.background = '#dbeafe30'
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget as HTMLAnchorElement
              el.style.borderColor = 'var(--border2)'
              el.style.color = 'var(--fg-muted)'
              el.style.background = 'transparent'
            }}
          >
            ↗
          </a>
        )}

        {/* EXPAND TOGGLE */}
        <button
          onClick={() => setNotesOpen(v => !v)}
          title={notesOpen ? 'Chiudi' : 'Espandi contenuto'}
          style={{
            background: notesOpen ? 'var(--accent-bg)' : 'transparent',
            border: `1px solid ${notesOpen ? '#c4b9f5' : 'var(--border2)'}`,
            borderRadius: 5,
            padding: '4px 8px',
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: notesOpen ? 'var(--accent)' : 'var(--fg-muted)',
            cursor: 'pointer',
            transition: 'all 0.12s',
            flexShrink: 0,
          }}
        >
          {notesOpen ? '▲' : '▼'}
        </button>

        {/* TIME */}
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--fg-dim)',
            flexShrink: 0,
          }}
        >
          {timeAgo(idea.created_at)}
        </div>

        {/* ACTIONS */}
        <div style={{ display: 'flex', gap: 5, alignItems: 'center', flexShrink: 0 }}>
          {tab === 'inbox' && (
            <button
              onClick={() => togglePublish.mutate(idea)}
              disabled={togglePublish.isPending}
              style={btnStyle('green')}
            >
              Pubblica
            </button>
          )}

          {tab === 'published' && (
            <button
              onClick={() => togglePublish.mutate(idea)}
              disabled={togglePublish.isPending}
              style={btnStyle('dim')}
            >
              Annulla
            </button>
          )}

          {(tab === 'inbox' || tab === 'published') && (
            <button onClick={onEdit} style={btnStyle('edit')}>
              Edit
            </button>
          )}

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

      {/* INLINE PANEL — summary + notes */}
      {notesOpen && (
        <div
          style={{
            margin: '0 12px 10px 64px',
            borderRadius: 8,
            border: '1px solid var(--border2)',
            overflow: 'hidden',
          }}
        >
          {/* Summary */}
          <div style={{ padding: '12px 16px', background: 'var(--surface2)' }}>
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                letterSpacing: '1.2px',
                textTransform: 'uppercase',
                color: 'var(--fg-dim)',
                marginBottom: 7,
              }}
            >
              Summary
            </div>
            <div
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: 14,
                lineHeight: 1.75,
                color: 'var(--fg)',
                whiteSpace: 'pre-wrap',
              }}
            >
              {idea.summary}
            </div>
          </div>

          {/* Details — schematic breakdown */}
          {idea.details && (
            <div style={{ padding: '12px 16px', background: 'var(--surface2)', borderTop: '1px solid var(--border2)' }}>
              <div
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  letterSpacing: '1.2px',
                  textTransform: 'uppercase',
                  color: 'var(--fg-dim)',
                  marginBottom: 7,
                }}
              >
                Dettagli
              </div>
              <div
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: 13,
                  lineHeight: 1.75,
                  color: 'var(--fg)',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {idea.details}
              </div>
            </div>
          )}

          {/* Source URL */}
          {idea.source_url && (
            <div
              style={{
                padding: '10px 16px',
                background: 'var(--surface2)',
                borderTop: '1px solid var(--border2)',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <div
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  letterSpacing: '1.2px',
                  textTransform: 'uppercase',
                  color: 'var(--fg-dim)',
                  flexShrink: 0,
                }}
              >
                Sorgente
              </div>
              <a
                href={idea.source_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  color: '#3b82f6',
                  textDecoration: 'none',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  flex: 1,
                  minWidth: 0,
                }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLAnchorElement).style.textDecoration = 'underline' }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLAnchorElement).style.textDecoration = 'none' }}
              >
                {idea.source_url}
              </a>
            </div>
          )}

          {/* Note private */}
          <div
            style={{
              padding: '12px 16px',
              background: idea.notes ? 'var(--accent-bg)' : 'var(--surface2)',
              borderTop: `1px solid ${idea.notes ? '#c4b9f5' : 'var(--border2)'}`,
            }}
          >
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                letterSpacing: '1.2px',
                textTransform: 'uppercase',
                color: idea.notes ? 'var(--accent)' : 'var(--fg-dim)',
                marginBottom: 7,
              }}
            >
              Note private
            </div>
            <div
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: 14,
                lineHeight: 1.75,
                color: idea.notes ? 'var(--fg)' : 'var(--fg-dim)',
                whiteSpace: 'pre-wrap',
                fontStyle: idea.notes ? 'normal' : 'italic',
              }}
            >
              {idea.notes ?? 'Nessuna nota — aprì Edit per aggiungerne una.'}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function btnStyle(variant: 'green' | 'dim' | 'edit' | 'trash' | 'red'): CSSProperties {
  const base: CSSProperties = {
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
    letterSpacing: '0.4px',
    padding: '5px 12px',
    borderRadius: 5,
    border: 'none',
    cursor: 'pointer',
    transition: 'all 0.12s',
    fontWeight: 500,
  }
  const styles: Record<typeof variant, CSSProperties> = {
    green: { ...base, background: 'var(--green-bg)', color: 'var(--green)',    border: '1px solid #86efac' },
    dim:   { ...base, background: 'var(--surface2)', color: 'var(--fg-muted)', border: '1px solid var(--border2)' },
    edit:  { ...base, background: 'var(--accent-bg)', color: 'var(--accent)',  border: '1px solid #c4b9f5' },
    trash: { ...base, background: 'transparent', color: 'var(--fg-dim)', border: '1px solid transparent', padding: '5px 7px' },
    red:   { ...base, background: 'var(--red-bg)', color: 'var(--red)',        border: '1px solid #fca5a5' },
  }
  return styles[variant]
}
