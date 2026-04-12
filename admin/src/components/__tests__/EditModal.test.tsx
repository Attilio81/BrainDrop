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

  it("mostra il titolo attuale nell'input", () => {
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
