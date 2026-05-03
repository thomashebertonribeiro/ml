import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { DashboardStats } from '../../types'

interface LevelChartProps {
  stats: DashboardStats
}

export function LevelChart({ stats }: LevelChartProps) {
  const data = Object.entries(stats.categories_by_level)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([level, count]) => ({ level: `Nível ${level}`, count }))

  if (data.length === 0) return null

  return (
    <div style={{ marginTop: '1.5rem' }}>
      <h3 style={{ marginBottom: '1rem' }}>Categorias por nível hierárquico</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="level" />
          <YAxis />
          <Tooltip formatter={(v: number) => v.toLocaleString('pt-BR')} />
          <Bar dataKey="count" fill="#2980b9" name="Categorias" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
