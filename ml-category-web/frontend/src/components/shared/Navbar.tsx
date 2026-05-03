import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

export function Navbar() {
  const { isAuthenticated, clearToken } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    clearToken()
    navigate('/login')
  }

  return (
    <nav style={{
      display: 'flex', alignItems: 'center', gap: '1.5rem',
      padding: '0.75rem 1.5rem', background: '#1a1a2e', color: '#fff',
    }}>
      <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>🛒 ML Categories</span>
      {isAuthenticated && (
        <>
          <Link to="/" style={{ color: '#ccc', textDecoration: 'none' }}>Dashboard</Link>
          <Link to="/browse" style={{ color: '#ccc', textDecoration: 'none' }}>Navegar</Link>
          <Link to="/search" style={{ color: '#ccc', textDecoration: 'none' }}>Buscar</Link>
          <Link to="/changes" style={{ color: '#ccc', textDecoration: 'none' }}>Histórico</Link>
          <button
            onClick={handleLogout}
            style={{
              marginLeft: 'auto', background: '#e74c3c', color: '#fff',
              border: 'none', borderRadius: 4, padding: '0.4rem 1rem', cursor: 'pointer',
            }}
          >
            Sair
          </button>
        </>
      )}
    </nav>
  )
}
