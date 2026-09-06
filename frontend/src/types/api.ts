export interface ApiResponse<T> {
  data: T
}

export interface PaginationMeta {
  page: number
  pageSize: number
  totalItems: number
  totalPages: number
}

export interface ListResponse<T> {
  data: T[]
  pagination: PaginationMeta
}

export interface ApiErrorBody {
  error?: {
    code?: string
    message?: string
    details?: Record<string, unknown>
    requestId?: string
  }
}
