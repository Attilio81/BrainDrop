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
