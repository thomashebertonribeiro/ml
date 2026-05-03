import { useQuery } from '@tanstack/react-query'
import { getDashboardStats } from '../api/dashboard'
import { StatsCards } from '../components/dashboard/StatsCards'
import { LevelChart } from '../components/dashboard/LevelChart'
import { ImportButton } from '../components/import/ImportButton'
import { ImportProgress } from '../components/import/ImportProgress'

export function DashboardPage() {
  const { data: stats, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: getDashboardStats,
    staleTime: 5 * 60 * 1000,
  })

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ margin: 0 }}>Dashboard</h2>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <ImportButton />
          <button
            onClick={() => refetch()}
            style={{ padding: '0.6rem 1rem', background: '#ecf0f1', border: '1px solid #bdc3c7', borderRadius: 4, cursor: 'pointer' }}
          >
            🔄 Atualizar
          </button>
        </div>
      </div>

      <ImportProgress />

      {isLoading && <p>Carregando estatísticas...</p>}
      {error && <p style={{ color: '#e74c3c' }}>Erro ao carregar estatísticas.</p>}
      {stats && (
        <>
          <StatsCards stats={stats} />
          <LevelChart stats={stats} />
        </>
      )}
    </div>
  )
}
