import type { Tab } from '@/types'

interface Props {
  activeTab: Tab
  inboxCount: number
  onTabChange: (tab: Tab) => void
}

const tabs: { id: Tab; label: string }[] = [
  { id: 'inbox', label: 'Inbox' },
  { id: 'published', label: 'Published' },
  { id: 'trash', label: 'Trash' },
]

export default function TabNav({ activeTab, inboxCount, onTabChange }: Props) {
  return (
    <div style={{ display: 'flex', alignItems: 'stretch', flex: 1 }}>
      {tabs.map((t) => {
        const isActive = t.id === activeTab
        return (
          <button
            key={t.id}
            data-tab={t.id}
            data-active={isActive}
            onClick={() => onTabChange(t.id)}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: isActive ? '2px solid var(--accent)' : '2px solid transparent',
              color: isActive ? 'var(--fg)' : 'var(--fg-muted)',
              fontFamily: 'var(--font-body)',
              fontSize: 14,
              fontWeight: isActive ? 600 : 400,
              letterSpacing: '0.2px',
              padding: '0 20px',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            {t.label}
            {t.id === 'inbox' && inboxCount > 0 && (
              <span
                data-testid="inbox-badge"
                style={{
                  background: 'var(--accent)',
                  color: '#fff',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  fontWeight: 600,
                  padding: '1px 7px',
                  borderRadius: 20,
                  letterSpacing: '0.3px',
                }}
              >
                {inboxCount}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
