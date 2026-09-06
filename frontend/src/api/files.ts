import type { ApiResponse } from '@/types/api'

import http from './http'

export interface FileSummary {
  id: string
  originalName: string
  contentType: string
  size: number
  downloadUrl: string
  createdAt: string
}

export async function uploadFile(file: File): Promise<FileSummary> {
  const formData = new FormData()
  formData.append('upload', file)
  const response = await http.post<ApiResponse<FileSummary>>('/files', formData)
  return response.data.data
}
