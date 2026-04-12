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
  it("mostra il titolo dell'idea", () => {
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
