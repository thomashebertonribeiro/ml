import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../api/auth'
import { useAuthStore } from '../store/authStore'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const setToken = useAuthStore((s) => s.setToken)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { access_token } = await login(email, password)
      setToken(access_token)
      navigate('/')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })
        ?.response?.data?.message ?? 'Erro ao fazer login.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '4rem auto', padding: '2rem', border: '1px solid #ddd', borderRadius: 8 }}>
      <h2>Entrar</h2>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <input
          type="email" placeholder="E-mail" value={email}
          onChange={(e) => setEmail(e.target.value)} required
          style={{ padding: '0.5rem', borderRadius: 4, border: '1px solid #ccc' }}
        />
        <input
          type="password" placeholder="Senha" value={password}
          onChange={(e) => setPassword(e.target.value)} required
          style={{ padding: '0.5rem', borderRadius: 4, border: '1px solid #ccc' }}
        />
        {error && <p style={{ color: '#e74c3c', margin: 0 }}>{error}</p>}
        <button
          type="submit" disabled={loading}
          style={{ padding: '0.6rem', background: '#2980b9', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
        >
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
      <p style={{ marginTop: '1rem', textAlign: 'center' }}>
        Não tem conta? <Link to="/register">Registrar</Link>
      </p>
    </div>
  )
}
