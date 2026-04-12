import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, act, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FilterBar from '@/components/FilterBar'
import { DEFAULT_FILTERS } from '@/types'

afterEach(() => vi.useRealTimers())

describe('FilterBar', () => {
  it('mostra input di testo, dropdown categoria, e tag chips', () => {
    render(
      <FilterBar
        filters={DEFAULT_FILTERS}
        availableTags={['llm', 'python']}
        onChange={vi.fn()}
      />
    )
    expect(screen.getByPlaceholderText(/cerca/i)).toBeInTheDocument()
    expect(screen.getByRole('combobox')).toBeInTheDocument()
    expect(screen.getByText('#llm')).toBeInTheDocument()
    expect(screen.getByText('#python')).toBeInTheDocument()
  })

  it('chiama onChange con il testo dopo il debounce (300ms)', () => {
    vi.useFakeTimers()
    const onChange = vi.fn()
    render(
      <FilterBar
        filters={DEFAULT_FILTERS}
        availableTags={[]}
        onChange={onChange}
      />
    )
    fireEvent.change(screen.getByPlaceholderText(/cerca/i), { target: { value: 'react' } })
    expect(onChange).not.toHaveBeenCalled()
    act(() => { vi.advanceTimersByTime(300) })
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ text: 'react' }))
  })

  it('click su tag chip attiva/disattiva il tag nei filtri', async () => {
    const onChange = vi.fn()
    render(
      <FilterBar
        filters={DEFAULT_FILTERS}
        availableTags={['llm']}
        onChange={onChange}
      />
    )
    await userEvent.click(screen.getByText('#llm'))
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ tags: ['llm'] }))
  })

  it('click su tag già attivo lo rimuove dai filtri', async () => {
    const onChange = vi.fn()
    render(
      <FilterBar
        filters={{ ...DEFAULT_FILTERS, tags: ['llm'] }}
        availableTags={['llm']}
        onChange={onChange}
      />
    )
    await userEvent.click(screen.getByText('#llm'))
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ tags: [] }))
  })
})
