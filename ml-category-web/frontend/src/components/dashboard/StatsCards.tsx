import type { DashboardStats } from '../../types'

interface StatsCardsProps {
  stats: DashboardStats
}

const Card = ({ label, value }: { label: string; value: string | number }) => (
  <div style={{
    background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8,
    padding: '1rem 1.5rem', minWidth: 160, textAlign: 'center',
  }}>
    <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#2980b9' }}>
      {typeof value === 'number' ? value.toLocaleString('pt-BR') : value}
    </div>
    <div style={{ color: '#666', fontSize: '0.9rem', marginTop: '0.25rem' }}>{label}</div>
  </div>
)

export function StatsCards({ stats }: StatsCardsProps) {
  const lastImport = stats.last_import_at
    ? new Date(stats.last_import_at).toLocaleString('pt-BR')
    : 'Nunca'

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
      <Card label="Total de categorias" value={stats.total_categories} />
      <Card label="Categorias raiz" value={stats.total_root_categories} />
      <Card label="Categorias folha" value={stats.total_leaf_categories} />
      <Card label="Profundidade máxima" value={stats.max_depth} />
      <Card label="Mudanças (30 dias)" value={stats.changes_last_30_days} />
      <Card label="Última importação" value={lastImport} />
    </div>
  )
}
