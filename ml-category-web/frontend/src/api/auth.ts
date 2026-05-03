import apiClient from './client'
import type { TokenResponse } from '../types'

export const login = async (email: string, password: string): Promise<TokenResponse> => {
  const { data } = await apiClient.post<TokenResponse>('/auth/login', { email, password })
  return data
}

export const register = async (email: string, password: string): Promise<TokenResponse> => {
  const { data } = await apiClient.post<TokenResponse>('/auth/register', { email, password })
  return data
}

export const refreshToken = async (access_token: string): Promise<TokenResponse> => {
  const { data } = await apiClient.post<TokenResponse>('/auth/refresh', { access_token })
  return data
}
