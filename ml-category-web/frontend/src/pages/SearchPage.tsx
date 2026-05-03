import { useState } from 'react'
import { SearchBar } from '../components/categories/SearchBar'
import { CategoryDetail } from '../components/categories/CategoryDetail'
import { useSearchCategories, useCategoryDetail } from '../hooks/useCategories'
import type { CategoryOut } from '../types'

export function SearchPage() {
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const { data, isLoading, error } = useSearchCategories(query, page)
  const { data: detail } = useCategoryDetail(selectedId)

  const handleSearch = (q: string) => {
    setQuery(q)
    setPage(1)
    setSelectedId(null)
  }

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 0

  return (
    <div style={{ padding: '1.5rem' }}>
      <h2 style={{ marginTop: 0 }}>Buscar Categorias</h2>
      <SearchBar onSearch={handleSearch} />

      <div style={{ display: 'flex', gap: '1.5rem', marginTop: '1.5rem' }}>
        {/* Results list */}
        <div style={{ flex: 1 }}>
          {isLoading && <p>Buscando...</p>}
          {error && <p style={{ color: '#e74c3c' }}>Erro na busca.</p>}
          {data && data.items.length === 0 && (
            <p style={{ color: '#888' }}>Nenhuma categoria encontrada para "{query}".</p>
          )}
          {data && data.items.length > 0 && (
            <>
              <p style={{ color: '#666', marginBottom: '0.75rem' }}>
                {data.total.toLocaleString()} resultado(s) para "{query}"
              </p>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {data.items.map((cat: CategoryOut) => (
                  <li
                    key={cat.id}
                    onClick={() => setSelectedId(cat.id)}
                    style={{
                      padding: '0.6rem 0.75rem', cursor: 'pointer', borderRadius: 4,
                      background: selectedId === cat.id ? '#e8f4fd' : 'transparent',
                      borderBottom: '1px solid #f0f0f0',
                    }}
                  >
                    <div style={{ fontWeight: 500 }}>{cat.name}</div>
                    <div style={{ fontSize: '0.8em', color: '#888' }}>
                      {cat.id} · Nível {cat.level}
                    </div>
                  </li>
                ))}
              </ul>
              {totalPages > 1 && (
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                  <button onClick={() => setPage(p => p - 1)} disabled={page <= 1}
                    style={{ padding: '0.3rem 0.8rem', cursor: 'pointer' }}>‹</button>
                  <span style={{ padding: '0.3rem 0.8rem' }}>Página {page} de {totalPages}</span>
                  <button onClick={() => setPage(p => p + 1)} disabled={page >= totalPages}
                    style={{ padding: '0.3rem 0.8rem', cursor: 'pointer' }}>›</button>
                </div>
              )}
            </>
          )}
        </div>

        {/* Detail panel */}
        {detail && (
          <div style={{ width: 380, flexShrink: 0 }}>
            <CategoryDetail category={detail} />
          </div>
        )}
      </div>
    </div>
  )
}
