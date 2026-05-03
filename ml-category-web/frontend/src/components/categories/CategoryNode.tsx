import { useState } from 'react'
import { useCategoryChildren } from '../../hooks/useCategories'
import type { CategoryOut } from '../../types'

interface CategoryNodeProps {
  category: CategoryOut
  onSelect: (category: CategoryOut) => void
  depth?: number
}

export function CategoryNode({ category, onSelect, depth = 0 }: CategoryNodeProps) {
  const [expanded, setExpanded] = useState(false)
  const { data: children, isLoading } = useCategoryChildren(expanded ? category.id : null)

  const hasChildren = category.children_count !== 0

  const toggle = () => {
    if (hasChildren !== false) setExpanded((prev) => !prev)
  }

  return (
    <div style={{ marginLeft: depth * 16 }}>
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: '0.4rem',
          padding: '0.3rem 0.5rem', cursor: 'pointer', borderRadius: 4,
          userSelect: 'none',
        }}
        onClick={() => onSelect(category)}
      >
        <span
          onClick={(e) => { e.stopPropagation(); toggle() }}
          style={{ width: 16, textAlign: 'center', color: '#666', fontSize: '0.8em' }}
        >
          {isLoading ? '⏳' : expanded ? '▼' : '▶'}
        </span>
        <span style={{ fontSize: '0.95rem' }}>{category.name}</span>
        <span style={{ color: '#aaa', fontSize: '0.8em', marginLeft: 'auto' }}>{category.id}</span>
      </div>
      {expanded && children && children.map((child) => (
        <CategoryNode key={child.id} category={child} onSelect={onSelect} depth={depth + 1} />
      ))}
    </div>
  )
}
