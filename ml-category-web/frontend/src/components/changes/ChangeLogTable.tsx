import type { ChangeLogOut } from '../../types'

interface ChangeLogTableProps {
  items: ChangeLogOut[]
  total: number
  page: number
  pageSize: number
  onPageChange: (page: number) => void
  onTypeFilter: (type: 'added' | 'removed' | undefined) => void
  typeFilter?: 'added' | 'removed'
}

export function ChangeLogTable({
  items, total, page, pageSize, onPageChange, onTypeFilter, typeFilter,
}: ChangeLogTableProps) {
  const totalPages = Math.ceil(total / pageSize)

  return (
    <div>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', alignItems: 'center' }}>
        <strong>Filtrar por tipo:</strong>
        <button
          onClick={() => onTypeFilter(undefined)}
          style={{ background: !typeFilter ? '#2980b9' : '#eee', color: !typeFilter ? '#fff' : '#333', border: 'none', borderRadius: 4, padding: '0.3rem 0.8rem', cursor: 'pointer' }}
        >Todos</button>
        <button
          onClick={() => onTypeFilter('added')}
          style={{ background: typeFilter === 'added' ? '#27ae60' : '#eee', color: typeFilter === 'added' ? '#fff' : '#333', border: 'none', borderRadius: 4, padding: '0.3rem 0.8rem', cursor: 'pointer' }}
        >Adicionados</button>
        <button
          onClick={() => onTypeFilter('removed')}
          style={{ background: typeFilter === 'removed' ? '#e74c3c' : '#eee', color: typeFilter === 'removed' ? '#fff' : '#333', border: 'none', borderRadius: 4, padding: '0.3rem 0.8rem', cursor: 'pointer' }}
        >Removidos</button>
        <span style={{ marginLeft: 'auto', color: '#666' }}>{total.toLocaleString()} registros</span>
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
        <thead>
          <tr style={{ background: '#f5f5f5' }}>
            <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Data</th>
            <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Tipo</th>
            <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Categoria</th>
            <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Categoria Pai</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} style={{ borderBottom: '1px solid #eee' }}>
              <td style={{ padding: '0.5rem', color: '#555' }}>
                {new Date(item.detected_at).toLocaleString('pt-BR')}
              </td>
              <td style={{ padding: '0.5rem' }}>
                <span style={{
                  background: item.change_type === 'added' ? '#d4edda' : '#f8d7da',
                  color: item.change_type === 'added' ? '#155724' : '#721c24',
                  padding: '0.2rem 0.5rem', borderRadius: 4, fontSize: '0.85em',
                }}>
                  {item.change_type === 'added' ? '+ Adicionado' : '− Removido'}
                </span>
              </td>
              <td style={{ padding: '0.5rem' }}>
                {item.category_name}
                <span style={{ color: '#aaa', fontSize: '0.8em', marginLeft: '0.4rem' }}>({item.category_id})</span>
              </td>
              <td style={{ padding: '0.5rem', color: '#666' }}>{item.parent_id ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', justifyContent: 'center' }}>
          <button onClick={() => onPageChange(page - 1)} disabled={page <= 1}
            style={{ padding: '0.3rem 0.8rem', cursor: 'pointer' }}>‹</button>
          <span style={{ padding: '0.3rem 0.8rem' }}>Página {page} de {totalPages}</span>
          <button onClick={() => onPageChange(page + 1)} disabled={page >= totalPages}
            style={{ padding: '0.3rem 0.8rem', cursor: 'pointer' }}>›</button>
        </div>
      )}
    </div>
  )
}
