import { useRootCategories } from '../../hooks/useCategories'
import { CategoryNode } from './CategoryNode'
import type { CategoryOut } from '../../types'

interface CategoryTreeProps {
  onSelect: (category: CategoryOut) => void
}

export function CategoryTree({ onSelect }: CategoryTreeProps) {
  const { data: roots, isLoading, error } = useRootCategories()

  if (isLoading) return <p style={{ padding: '1rem', color: '#666' }}>Carregando categorias...</p>
  if (error) return <p style={{ padding: '1rem', color: '#e74c3c' }}>Erro ao carregar categorias.</p>
  if (!roots || roots.length === 0) {
    return (
      <p style={{ padding: '1rem', color: '#888' }}>
        Nenhuma categoria encontrada. Inicie uma importação no Dashboard.
      </p>
    )
  }

  return (
    <div style={{ overflowY: 'auto', height: '100%', padding: '0.5rem' }}>
      {roots.map((cat) => (
        <CategoryNode key={cat.id} category={cat} onSelect={onSelect} />
      ))}
    </div>
  )
}
