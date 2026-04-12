import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TabNav from '@/components/TabNav'

describe('TabNav', () => {
  it('mostra 3 tab: Inbox, Published, Trash', () => {
    render(<TabNav activeTab="inbox" inboxCount={0} onTabChange={vi.fn()} />)
    expect(screen.getByText('Inbox')).toBeInTheDocument()
    expect(screen.getByText('Published')).toBeInTheDocument()
    expect(screen.getByText('Trash')).toBeInTheDocument()
  })

  it('mostra il badge numerico solo su Inbox quando > 0', () => {
    render(<TabNav activeTab="inbox" inboxCount={7} onTabChange={vi.fn()} />)
    expect(screen.getByText('7')).toBeInTheDocument()
  })

  it('non mostra il badge se inboxCount è 0', () => {
    render(<TabNav activeTab="inbox" inboxCount={0} onTabChange={vi.fn()} />)
    expect(screen.queryByTestId('inbox-badge')).not.toBeInTheDocument()
  })

  it('chiama onTabChange con il tab corretto al click', async () => {
    const onChange = vi.fn()
    render(<TabNav activeTab="inbox" inboxCount={0} onTabChange={onChange} />)
    await userEvent.click(screen.getByText('Published'))
    expect(onChange).toHaveBeenCalledWith('published')
  })

  it('applica stile attivo al tab selezionato', () => {
    render(<TabNav activeTab="published" inboxCount={0} onTabChange={vi.fn()} />)
    const publishedTab = screen.getByText('Published').closest('[data-tab]')
    expect(publishedTab).toHaveAttribute('data-active', 'true')
  })
})
