import type { ApiResponse } from '@/types/api'
import type { TaskSummary } from '@/types/resources'

import http from './http'

export interface ExportTaskPayload {
  reportType: 'INVENTORY_DETAIL' | 'ALERT_DETAIL'
  filters: {
    warehouseId?: string
    startDate?: string
    endDate?: string
  }
}

export async function submitExportTask(payload: ExportTaskPayload): Promise<TaskSummary> {
  const response = await http.post<ApiResponse<TaskSummary>>('/export-tasks', payload)
  return response.data.data
}

export async function getExportTask(taskId: string): Promise<TaskSummary> {
  const response = await http.get<ApiResponse<TaskSummary>>(`/tasks/${taskId}`)
  return response.data.data
}
