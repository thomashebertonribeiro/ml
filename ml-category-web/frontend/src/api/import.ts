import apiClient from './client'
import type { ImportStartResponse, ImportStatusOut } from '../types'

export const startImport = async (): Promise<ImportStartResponse> => {
  const { data } = await apiClient.post<ImportStartResponse>('/import/start')
  return data
}

export const getImportStatus = async (): Promise<ImportStatusOut> => {
  const { data } = await apiClient.get<ImportStatusOut>('/import/status')
  return data
}
