import { useState } from 'react'
import { startImport } from '../../api/import'
import { useImportStore } from '../../store/importStore'

export function ImportButton() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { isImporting, setImporting, setJobId } = useImportStore()

  const handleImport = async () => {
    setError('')
    setLoading(true)
    try {
      const { job_id } = await startImport()
      setJobId(job_id)
      setImporting(true)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })
        ?.response?.data?.message ?? 'Erro ao iniciar importação.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <button
        onClick={handleImport}
        disabled={loading || isImporting}
        style={{
          padding: '0.6rem 1.4rem', background: '#8e44ad', color: '#fff',
          border: 'none', borderRadius: 4, cursor: 'pointer', fontWeight: 600,
        }}
      >
        {loading ? 'Iniciando...' : isImporting ? '⏳ Importando...' : '📥 Importar Todas as Categorias'}
      </button>
      {error && <p style={{ color: '#e74c3c', marginTop: '0.5rem', fontSize: '0.9em' }}>{error}</p>}
    </div>
  )
}
