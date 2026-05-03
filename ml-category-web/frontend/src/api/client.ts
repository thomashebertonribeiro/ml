import axios from 'axios'
import { useAuthStore } from '../store/authStore'

// Em produção com Traefik, o frontend e backend estão no mesmo domínio.
// O Traefik roteia /api/* → backend (removendo o prefixo /api).
// Em desenvolvimento, usa VITE_API_URL diretamente.
const isProd = import.meta.env.PROD
const baseURL = isProd
  ? '/api'
  : (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'

const apiClient = axios.create({ baseURL })

// Request interceptor: add Authorization header
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: redirect to /login on 401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().clearToken()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
