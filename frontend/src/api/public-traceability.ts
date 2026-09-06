import type { ApiResponse } from '@/types/api'
import type { PublicTraceSummary } from '@/types/resources'

import http from './http'

export function getPublicQrCodeUrl(traceCode: string): string {
  const baseUrl = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1').replace(/\/$/, '')
  return `${baseUrl}/public/qr-codes/${encodeURIComponent(traceCode)}.png`
}

export async function getPublicTrace(traceCode: string): Promise<PublicTraceSummary> {
  const response = await http.get<ApiResponse<PublicTraceSummary>>(
    `/public/traces/${encodeURIComponent(traceCode)}`,
  )
  return response.data.data
}
