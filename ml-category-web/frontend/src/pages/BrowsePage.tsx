import { useState } from 'react'
import { CategoryTree } from '../components/categories/CategoryTree'
import { CategoryDetail } from '../components/categories/CategoryDetail'
import { useCategoryDetail } from '../hooks/useCategories'
import type { CategoryOut } from '../types'

export function BrowsePage() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const { data: detail } = useCategoryDetail(selectedId)

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 56px)', overflow: 'hidden' }}>
      {/* Left: tree */}
      <div style={{ width: 360, borderRight: '1px solid #e0e0e0', overflowY: 'auto', padding: '0.5rem' }}>
        <h3 style={{ margin: '0.5rem 0 0.75rem 0.5rem' }}>Categorias</h3>
        <CategoryTree onSelect={(cat: CategoryOut) => setSelectedId(cat.id)} />
      </div>

      {/* Right: detail */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
        {detail ? (
          <CategoryDetail category={detail} />
        ) : (
          <div style={{ color: '#888', marginTop: '2rem', textAlign: 'center' }}>
            <p>Selecione uma categoria na árvore para ver os detalhes.</p>
          </div>
        )}
      </div>
    </div>
  )
}
