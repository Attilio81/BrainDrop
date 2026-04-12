import { useEffect, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
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

  useEffect(() => {
    if (idea) {
      setTitle(idea.title)
      setSummary(idea.summary)
      setCategory(idea.category)
      setTags(idea.tags)
      setNotes(idea.notes ?? '')
    }
  }, [idea])

  useEffect(() => {
    if (!idea) return
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [idea, onClose])

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
      { id: idea!.id, patch },
      { onSuccess: onClose }
    )
  }

  return (
    <div
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(24, 24, 44, 0.18)',
        backdropFilter: 'blur(6px)',
        WebkitBackdropFilter: 'blur(6px)',
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
      }}
    >
      <div
        style={{
          background: 'var(--surface)',
          borderRadius: 16,
          border: '1px solid var(--border)',
          width: '100%',
          maxWidth: 960,
          maxHeight: '92vh',
          overflow: 'auto',
          boxShadow: '0 32px 80px rgba(24,24,44,0.14)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* HEADER */}
        <div
          style={{
            padding: '22px 32px',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexShrink: 0,
          }}
        >
          <h2
            style={{
              fontFamily: 'var(--font-display)',
              fontWeight: 800,
              fontSize: 18,
              letterSpacing: 2,
              textTransform: 'uppercase',
              color: 'var(--fg)',
              margin: 0,
            }}
          >
            Edit Idea
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: '1px solid var(--border)',
              borderRadius: 6,
              width: 32,
              height: 32,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--fg-muted)',
              fontSize: 16,
              cursor: 'pointer',
              lineHeight: 1,
            }}
          >
            ✕
          </button>
        </div>

        {/* BODY: 2 columns */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 0,
            flex: 1,
            overflow: 'auto',
          }}
        >
          {/* LEFT: titolo + summary + note */}
          <div
            style={{
              padding: '28px 32px',
              borderRight: '1px solid var(--border)',
              display: 'flex',
              flexDirection: 'column',
              gap: 22,
            }}
          >
            <FieldGroup label="Titolo">
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={inputStyle}
              />
            </FieldGroup>

            <FieldGroup label="Summary">
              <textarea
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                style={{ ...inputStyle, minHeight: 180, resize: 'vertical', lineHeight: 1.65 }}
              />
            </FieldGroup>

            <FieldGroup label="Note private — mai pubblicate">
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Note personali…"
                style={{
                  ...inputStyle,
                  minHeight: 140,
                  resize: 'vertical',
                  lineHeight: 1.65,
                  fontStyle: notes ? 'normal' : 'italic',
                }}
              />
            </FieldGroup>
          </div>

          {/* RIGHT: categoria + tags */}
          <div
            style={{
              padding: '28px 32px',
              display: 'flex',
              flexDirection: 'column',
              gap: 22,
            }}
          >
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

            <FieldGroup label="Tags — premi Invio per aggiungere">
              <div
                style={{
                  display: 'flex',
                  gap: 6,
                  flexWrap: 'wrap',
                  background: 'var(--surface2)',
                  border: '1px solid var(--border2)',
                  borderRadius: 8,
                  padding: '10px 12px',
                  minHeight: 50,
                  alignItems: 'flex-start',
                  alignContent: 'flex-start',
                }}
              >
                {tags.map((tag) => (
                  <span
                    key={tag}
                    style={{
                      background: 'var(--accent-bg)',
                      color: 'var(--accent)',
                      border: '1px solid #c4b9f5',
                      borderRadius: 20,
                      padding: '3px 10px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: 12,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 5,
                      fontWeight: 500,
                    }}
                  >
                    #{tag}
                    <span
                      onClick={() => removeTag(tag)}
                      style={{ color: 'var(--accent)', cursor: 'pointer', opacity: 0.7, fontSize: 14, lineHeight: 1 }}
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
                    color: 'var(--fg-muted)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    minWidth: 80,
                    flex: 1,
                  }}
                />
              </div>
            </FieldGroup>
          </div>
        </div>

        {/* FOOTER */}
        <div
          style={{
            padding: '18px 32px',
            borderTop: '1px solid var(--border)',
            display: 'flex',
            gap: 10,
            justifyContent: 'flex-end',
            flexShrink: 0,
            background: 'var(--surface)',
          }}
        >
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: '1px solid var(--border2)',
              color: 'var(--fg-muted)',
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              fontWeight: 500,
              padding: '9px 20px',
              borderRadius: 7,
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
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              fontWeight: 600,
              padding: '9px 28px',
              borderRadius: 7,
              cursor: updateIdea.isPending ? 'not-allowed' : 'pointer',
              letterSpacing: '0.4px',
              opacity: updateIdea.isPending ? 0.7 : 1,
            }}
          >
            Salva
          </button>
        </div>
      </div>
    </div>
  )
}

function FieldGroup({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 10,
          letterSpacing: '1.5px',
          textTransform: 'uppercase',
          color: 'var(--fg-dim)',
          fontWeight: 500,
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
  borderRadius: 8,
  padding: '10px 14px',
  color: 'var(--fg)',
  fontFamily: 'var(--font-body)',
  fontSize: 15,
  outline: 'none',
  width: '100%',
}
