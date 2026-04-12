import { useState } from 'react'
import { supabase } from '@/lib/supabase'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { shouldCreateUser: true },
    })
    setLoading(false)
    if (error) {
      setError(error.message)
    } else {
      setSent(true)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg)',
    }}>
      <div style={{
        width: 360,
        padding: '2rem',
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 12,
      }}>
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: '1.5rem',
          fontWeight: 700,
          color: 'var(--fg)',
          marginBottom: '0.5rem',
        }}>
          BrainDrop Admin
        </h1>
        <p style={{ color: 'var(--fg-muted)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
          Inserisci la tua email per ricevere il magic link.
        </p>

        {sent ? (
          <p style={{ color: 'var(--accent)', fontSize: '0.9rem' }}>
            Email inviata! Controlla la tua casella e clicca il link.
          </p>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <input
              type="email"
              required
              placeholder="tua@email.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              style={{
                padding: '0.625rem 0.875rem',
                background: 'var(--bg)',
                border: '1px solid var(--border)',
                borderRadius: 6,
                color: 'var(--fg)',
                fontSize: '0.875rem',
                outline: 'none',
              }}
            />
            {error && (
              <p style={{ color: '#f87171', fontSize: '0.8rem' }}>{error}</p>
            )}
            <button
              type="submit"
              disabled={loading}
              style={{
                padding: '0.625rem',
                background: 'var(--accent)',
                border: 'none',
                borderRadius: 6,
                color: '#fff',
                fontFamily: 'var(--font-body)',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? 'Invio...' : 'Invia magic link'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
