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
              color: isActive ? 'var(--text)' : 'var(--text-muted)',
              fontFamily: 'DM Sans, sans-serif',
              fontSize: 12,
              fontWeight: 500,
              letterSpacing: '0.3px',
              padding: '0 18px',
              display: 'flex',
              alignItems: 'center',
              gap: 7,
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
                  fontFamily: 'DM Mono, monospace',
                  fontSize: 9,
                  fontWeight: 500,
                  padding: '1px 6px',
                  borderRadius: 20,
                  letterSpacing: '0.5px',
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
