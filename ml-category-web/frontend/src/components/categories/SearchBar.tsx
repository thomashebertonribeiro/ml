import { useState, useCallback } from 'react'

interface SearchBarProps {
  onSearch: (query: string) => void
  placeholder?: string
}

export function SearchBar({ onSearch, placeholder = 'Buscar categorias...' }: SearchBarProps) {
  const [value, setValue] = useState('')

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      if (value.trim().length >= 2) onSearch(value.trim())
    },
    [value, onSearch]
  )

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        style={{ flex: 1, padding: '0.5rem 0.75rem', borderRadius: 4, border: '1px solid #ccc', fontSize: '1rem' }}
      />
      <button
        type="submit"
        disabled={value.trim().length < 2}
        style={{
          padding: '0.5rem 1.2rem', background: '#2980b9', color: '#fff',
          border: 'none', borderRadius: 4, cursor: 'pointer',
        }}
      >
        Buscar
      </button>
    </form>
  )
}
