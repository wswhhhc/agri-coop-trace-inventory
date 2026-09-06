export interface ApiResponse<T> {
  data: T
}

export interface ApiErrorBody {
  error?: {
    code?: string
    message?: string
    details?: Record<string, unknown>
    requestId?: string
  }
}
