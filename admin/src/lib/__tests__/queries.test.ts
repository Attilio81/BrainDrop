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
