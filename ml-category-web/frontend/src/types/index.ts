export interface PathNode {
  id: string
  name: string
}

export interface CategoryOut {
  id: string
  name: string
  parent_id: string | null
  level: number
  total_items: number
  path_from_root: PathNode[]
}

export interface CategoryDetail extends CategoryOut {
  children: CategoryOut[]
}

export interface SearchResponse {
  items: CategoryOut[]
  total: number
  page: number
  page_size: number
}

export interface ImportStartResponse {
  job_id: string
  status: string
}

export interface ImportStatusOut {
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  processed: number
  total_estimated: number
  started_at: string | null
  finished_at: string | null
  error_count: number
}

export interface SSEProgressEvent {
  processed: number
  total_estimated: number
  percent: number
  current_category: string
  status: string
  added?: number
  removed?: number
  error_count?: number
}

export interface DashboardStats {
  total_categories: number
  total_root_categories: number
  total_leaf_categories: number
  max_depth: number
  last_import_at: string | null
  changes_last_30_days: number
  categories_by_level: Record<number, number>
}

export interface ChangeLogOut {
  id: number
  change_type: 'added' | 'removed'
  category_id: string
  category_name: string
  parent_id: string | null
  detected_at: string
  import_job_id: string
}

export interface ChangeSummaryItem {
  month: string
  added: number
  removed: number
}

export interface SchedulerStatus {
  active: boolean
  last_run_at: string | null
  next_run_at: string | null
  last_run_result: string | null
  interval_hours: number
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}
