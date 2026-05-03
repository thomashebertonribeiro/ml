import apiClient from './client'
import type { ChangeLogOut, ChangeSummaryItem } from '../types'

interface ChangeLogResponse {
  items: ChangeLogOut[]
  total: number
  page: number
  page_size: number
}

export const getChanges = async (params?: {
  type?: 'added' | 'removed'
  category_id?: string
  from_date?: string
  to_date?: string
  page?: number
  page_size?: number
}): Promise<ChangeLogResponse> => {
  const { data } = await apiClient.get<ChangeLogResponse>('/changes/', { params })
  return data
}

export const getChangesSummary = async (): Promise<ChangeSummaryItem[]> => {
  const { data } = await apiClient.get<ChangeSummaryItem[]>('/changes/summary')
  return data
}
