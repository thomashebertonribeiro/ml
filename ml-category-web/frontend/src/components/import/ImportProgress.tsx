import { useEffect } from 'react'
import { useSSE } from '../../hooks/useSSE'
import { useImportStore } from '../../store/importStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function ImportProgress() {
  const { isImporting, jobId, setProgress, setImporting } = useImportStore()
  const sseUrl = isImporting && jobId ? `${API_URL}/import/progress` : null
  const { data, error } = useSSE(sseUrl)

  useEffect(() => {
    if (data) {
      setProgress(data)
      if (data.status === 'completed' || data.status === 'failed') {
        setImporting(false)
      }
    }
  }, [data, setProgress, setImporting])

  if (!isImporting && !data) return null

  const percent = data?.percent ?? 0
  const processed = data?.processed ?? 0
  const total = data?.total_estimated ?? 0
  const current = data?.current_category ?? ''
  const status = data?.status ?? 'running'

  return (
    <div style={{
      padding: '1rem', background: '#f0f8ff', border: '1px solid #b3d9ff',
      borderRadius: 8, marginBottom: '1rem',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
        <strong>
          {status === 'completed' ? '✅ Importação concluída!' :
           status === 'failed' ? '❌ Importação falhou' :
           '⏳ Importando categorias...'}
        </strong>
        <span style={{ color: '#555' }}>{processed.toLocaleString()} / {total.toLocaleString()}</span>
      </div>
      <div style={{ background: '#ddd', borderRadius: 4, height: 12, overflow: 'hidden' }}>
        <div style={{
          width: `${Math.min(percent, 100)}%`, height: '100%',
          background: status === 'completed' ? '#27ae60' : status === 'failed' ? '#e74c3c' : '#2980b9',
          transition: 'width 0.3s ease',
        }} />
      </div>
      {current && status === 'running' && (
        <p style={{ margin: '0.5rem 0 0', fontSize: '0.85em', color: '#666' }}>
          Processando: {current}
        </p>
      )}
      {error && <p style={{ color: '#e74c3c', margin: '0.5rem 0 0', fontSize: '0.85em' }}>{error}</p>}
    </div>
  )
}
