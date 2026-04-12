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
              color: 'var(--fg)',
            }}
          >
            Edit idea
          </SheetTitle>
        </SheetHeader>

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
            style={{ ...inputStyle, minHeight: 80, resize: 'vertical', lineHeight: 1.5 }}
          />
        </FieldGroup>

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

        <FieldGroup label="Note private — mai pubblicate">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Note personali…"
            style={{
              ...inputStyle,
              minHeight: 64,
              resize: 'vertical',
              lineHeight: 1.5,
              fontStyle: notes ? 'normal' : 'italic',
            }}
          />
        </FieldGroup>

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
          color: 'var(--fg-dim)',
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
  color: 'var(--fg)',
  fontFamily: 'DM Sans, sans-serif',
  fontSize: 13,
  outline: 'none',
  width: '100%',
}
