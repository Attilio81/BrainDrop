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
        borderBottom: '1px solid var(--border)',
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
          padding: '7px 13px',
          color: 'var(--fg)',
          fontFamily: 'var(--font-body)',
          fontSize: 13,
          width: 240,
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
          padding: '7px 10px',
          color: filters.category ? 'var(--fg)' : 'var(--fg-muted)',
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
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
              border: `1px solid ${isActive ? '#c4b9f5' : 'var(--border2)'}`,
              borderRadius: 20,
              padding: '4px 12px',
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              color: isActive ? 'var(--accent)' : 'var(--fg-muted)',
              cursor: 'pointer',
              transition: 'all 0.12s',
              fontWeight: isActive ? 500 : 400,
            }}
          >
            #{tag}
          </button>
        )
      })}
    </div>
  )
}
