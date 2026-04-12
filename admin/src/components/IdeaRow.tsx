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
  )
}

function btnStyle(variant: 'green' | 'dim' | 'edit' | 'trash' | 'red'): CSSProperties {
  const base: CSSProperties = {
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
