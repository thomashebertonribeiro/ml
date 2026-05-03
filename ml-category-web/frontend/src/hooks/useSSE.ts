import { useEffect, useRef, useState } from 'react'
import { useAuthStore } from '../store/authStore'
import type { SSEProgressEvent } from '../types'

interface UseSSEResult {
  data: SSEProgressEvent | null
  error: string | null
  connected: boolean
}

/**
 * Hook that connects to a Server-Sent Events endpoint.
 * Automatically closes the connection when the component unmounts
 * or when a terminal status (completed/failed) is received.
 */
export function useSSE(url: string | null): UseSSEResult {
  const [data, setData] = useState<SSEProgressEvent | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [connected, setConnected] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)
  const token = useAuthStore((s) => s.token)

  useEffect(() => {
    if (!url || !token) return

    // EventSource doesn't support custom headers natively.
    // We append the token as a query param as a workaround.
    // The backend should accept ?token= as an alternative to the Authorization header.
    const fullUrl = `${url}?token=${encodeURIComponent(token)}`
    const es = new EventSource(fullUrl)
    eventSourceRef.current = es

    es.onopen = () => setConnected(true)

    es.onmessage = (event) => {
      try {
        const parsed: SSEProgressEvent = JSON.parse(event.data)
        setData(parsed)
        if (parsed.status === 'completed' || parsed.status === 'failed') {
          es.close()
          setConnected(false)
        }
      } catch {
        // ignore parse errors
      }
    }

    es.onerror = () => {
      setError('Conexão SSE perdida.')
      setConnected(false)
      es.close()
    }

    return () => {
      es.close()
      setConnected(false)
    }
  }, [url, token])

  return { data, error, connected }
}
