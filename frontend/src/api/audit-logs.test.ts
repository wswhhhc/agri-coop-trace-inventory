import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { getAuditLog, listAuditLogs } from './audit-logs'

vi.mock('./http', () => ({
  default: { get: vi.fn() },
}))

describe('audit logs api', () => {
  beforeEach(() => vi.clearAllMocks())

  it('lists audit logs', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [] } })

    await expect(listAuditLogs()).resolves.toEqual([])
    expect(http.get).toHaveBeenCalledWith('/audit-logs', {
      params: { page: 1, pageSize: 10 },
    })
  })

  it('lists audit logs with filters', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [] } })

    await listAuditLogs({ action: 'CREATE_BATCH', result: 'FAILURE' })
    expect(http.get).toHaveBeenCalledWith('/audit-logs', {
      params: { page: 1, pageSize: 10, action: 'CREATE_BATCH', result: 'FAILURE' },
    })
  })

  it('gets an audit log detail', async () => {
    const log = { id: 'log-1', action: 'CREATE_BATCH', detail: { batchId: 'batch-1' } }
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: log } })

    await expect(getAuditLog('log-1')).resolves.toEqual(log)
    expect(http.get).toHaveBeenCalledWith('/audit-logs/log-1')
  })
})
