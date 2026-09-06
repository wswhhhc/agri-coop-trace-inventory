import axios from 'axios'

import type { ApiErrorBody } from '@/types/api'

export function getApiErrorMessage(error: unknown, fallback = '请求失败，请稍后重试'): string {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    return error.response?.data.error?.message ?? fallback
  }
  return fallback
}
