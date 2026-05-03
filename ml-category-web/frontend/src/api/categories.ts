import apiClient from './client'
import type { CategoryDetail, CategoryOut, SearchResponse } from '../types'

export const getRootCategories = async (): Promise<CategoryOut[]> => {
  const { data } = await apiClient.get<CategoryOut[]>('/categories/')
  return data
}

export const getCategoryDetail = async (id: string): Promise<CategoryDetail> => {
  const { data } = await apiClient.get<CategoryDetail>(`/categories/${id}`)
  return data
}

export const getCategoryChildren = async (id: string): Promise<CategoryOut[]> => {
  const { data } = await apiClient.get<CategoryOut[]>(`/categories/${id}/children`)
  return data
}

export const searchCategories = async (
  q: string,
  page = 1,
  pageSize = 50
): Promise<SearchResponse> => {
  const { data } = await apiClient.get<SearchResponse>('/categories/search', {
    params: { q, page, page_size: pageSize },
  })
  return data
}

// Public API (no auth)
export const getPublicRootCategories = async (): Promise<CategoryOut[]> => {
  const { data } = await apiClient.get<CategoryOut[]>('/public/categories')
  return data
}

export const searchPublicCategories = async (
  q: string,
  page = 1,
  pageSize = 50
): Promise<SearchResponse> => {
  const { data } = await apiClient.get<SearchResponse>('/public/categories/search', {
    params: { q, page, page_size: pageSize },
  })
  return data
}
