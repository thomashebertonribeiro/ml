import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getChanges } from '../api/changes'
import { ChangeLogTable } from '../components/changes/ChangeLogTable'

export function ChangesPage() {
  const [page, setPage] = useState(1)
  const [typeFilter, setTypeFilter] = useState<'added' | 'removed' | undefined>(undefined)

  const { data, isLoading, error } = useQuery({
    queryKey: ['changes', page, typeFilter],
    queryFn: () => getChanges({ page, page_size: 50, type: typeFilter }),
    staleTime: 60 * 1000,
  })

  const handleTypeFilter = (type: 'added' | 'removed' | undefined) => {
    setTypeFilter(type)
    setPage(1)
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <h2 style={{ marginTop: 0 }}>Histórico de Mudanças</h2>
      <p style={{ color: '#666', marginBottom: '1.5rem' }}>
        Registro de categorias adicionadas e removidas detectadas durante as importações.
      </p>

      {isLoading && <p>Carregando histórico...</p>}
      {error && <p style={{ color: '#e74c3c' }}>Erro ao carregar histórico.</p>}
      {data && (
        <ChangeLogTable
          items={data.items}
          total={data.total}
          page={page}
          pageSize={50}
          onPageChange={setPage}
          onTypeFilter={handleTypeFilter}
          typeFilter={typeFilter}
        />
      )}
    </div>
  )
}
