import type { CategoryOut } from '../../types'

interface CategoryDetailProps {
  category: CategoryOut & { children?: CategoryOut[] }
}

export function CategoryDetail({ category }: CategoryDetailProps) {
  const path = category.path_from_root.map((p) => p.name).join(' › ')

  return (
    <div style={{ padding: '1rem', background: '#f9f9f9', borderRadius: 8, height: '100%' }}>
      <h3 style={{ marginTop: 0 }}>{category.name}</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <tbody>
          <tr>
            <td style={{ fontWeight: 600, paddingRight: '1rem', paddingBottom: '0.5rem' }}>ID</td>
            <td style={{ fontFamily: 'monospace', paddingBottom: '0.5rem' }}>{category.id}</td>
          </tr>
          <tr>
            <td style={{ fontWeight: 600, paddingRight: '1rem', paddingBottom: '0.5rem' }}>Nível</td>
            <td style={{ paddingBottom: '0.5rem' }}>{category.level}</td>
          </tr>
          <tr>
            <td style={{ fontWeight: 600, paddingRight: '1rem', paddingBottom: '0.5rem' }}>Total de itens</td>
            <td style={{ paddingBottom: '0.5rem' }}>{category.total_items.toLocaleString('pt-BR')}</td>
          </tr>
          <tr>
            <td style={{ fontWeight: 600, paddingRight: '1rem', paddingBottom: '0.5rem' }}>Caminho</td>
            <td style={{ paddingBottom: '0.5rem', color: '#555' }}>{path || category.name}</td>
          </tr>
        </tbody>
      </table>
      {category.children && category.children.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <strong>Subcategorias diretas ({category.children.length})</strong>
          <ul style={{ marginTop: '0.5rem', paddingLeft: '1.2rem' }}>
            {category.children.map((child) => (
              <li key={child.id} style={{ marginBottom: '0.25rem' }}>
                {child.name} <span style={{ color: '#999', fontSize: '0.85em' }}>({child.id})</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
