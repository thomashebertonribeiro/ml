import { create } from 'zustand'
import type { SSEProgressEvent } from '../types'

interface ImportState {
  isImporting: boolean
  progress: SSEProgressEvent | null
  jobId: string | null
  setImporting: (importing: boolean) => void
  setProgress: (progress: SSEProgressEvent) => void
  setJobId: (jobId: string) => void
  reset: () => void
}

export const useImportStore = create<ImportState>((set) => ({
  isImporting: false,
  progress: null,
  jobId: null,
  setImporting: (importing) => set({ isImporting: importing }),
  setProgress: (progress) => set({ progress }),
  setJobId: (jobId) => set({ jobId }),
  reset: () => set({ isImporting: false, progress: null, jobId: null }),
}))
