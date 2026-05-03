import apiClient from './client'
import type { DashboardStats } from '../types'

export const getDashboardStats = async (): Promise<DashboardStats> => {
  const { data } = await apiClient.get<DashboardStats>('/dashboard/stats')
  return data
}
