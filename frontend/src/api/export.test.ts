import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { downloadExportFile, getExportTask, submitExportTask } from './export'

vi.mock('./http', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

describe('export api', () => {
  beforeEach(() => vi.clearAllMocks())

  it('submits an export task', async () => {
    const payload = { reportType: 'INVENTORY_DETAIL' as const, filters: {} }
    vi.mocked(http.post).mockResolvedValueOnce({
      data: { data: { id: 'task-1', taskType: 'EXPORT_REPORT', status: 'PENDING' } },
    })

    await expect(submitExportTask(payload)).resolves.toMatchObject({
      id: 'task-1',
      status: 'PENDING',
    })
    expect(http.post).toHaveBeenCalledWith('/export-tasks', payload)
  })

  it('gets an export task', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: { data: { id: 'task-1', status: 'SUCCESS' } },
    })

    await expect(getExportTask('task-1')).resolves.toMatchObject({ status: 'SUCCESS' })
    expect(http.get).toHaveBeenCalledWith('/tasks/task-1')
  })

  it('downloads an export file as a blob', async () => {
    const blob = new Blob(['file'])
    vi.mocked(http.get).mockResolvedValueOnce({ data: blob })

    await expect(downloadExportFile('task-1')).resolves.toBe(blob)
    expect(http.get).toHaveBeenCalledWith('/export-files/task-1', { responseType: 'blob' })
  })
})
