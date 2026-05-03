import { useQuery } from '@tanstack/react-query'
import {
  getCategoryChildren,
  getCategoryDetail,
  getRootCategories,
  searchCategories,
} from '../api/categories'

export const useRootCategories = () =>
  useQuery({
    queryKey: ['categories', 'roots'],
    queryFn: getRootCategories,
    staleTime: 5 * 60 * 1000, // 5 min
  })

export const useCategoryDetail = (id: string | null) =>
  useQuery({
    queryKey: ['categories', id],
    queryFn: () => getCategoryDetail(id!),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  })

export const useCategoryChildren = (id: string | null) =>
  useQuery({
    queryKey: ['categories', id, 'children'],
    queryFn: () => getCategoryChildren(id!),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  })

export const useSearchCategories = (q: string, page = 1, pageSize = 50) =>
  useQuery({
    queryKey: ['categories', 'search', q, page, pageSize],
    queryFn: () => searchCategories(q, page, pageSize),
    enabled: q.trim().length >= 2,
    staleTime: 5 * 60 * 1000,
  })
