import { create } from 'zustand'

interface AuthState {
  token: string | null
  isAuthenticated: boolean
  setToken: (token: string) => void
  clearToken: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null, // NUNCA persistir em localStorage
  isAuthenticated: false,
  setToken: (token) => set({ token, isAuthenticated: true }),
  clearToken: () => set({ token: null, isAuthenticated: false }),
}))
