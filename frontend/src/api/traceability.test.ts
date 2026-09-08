import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { listTraceEvents, listTraceEventsPage } from './traceability'

vi.mock('./http', () => ({
  default: { get: vi.fn() },
}))

describe('traceability api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('lists internal trace events in chronological order', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [] } })

    await expect(listTraceEvents('batch-1')).resolves.toEqual([])
    expect(http.get).toHaveBeenCalledWith('/batches/batch-1/trace-events', {
      params: { page: 1, pageSize: 10, sortBy: 'eventTime', sortOrder: 'ASC' },
    })
  })

  it('sends an event type filter', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [] } })

    await listTraceEventsPage('batch-1', { eventType: 'INSPECTION' })

    expect(http.get).toHaveBeenCalledWith('/batches/batch-1/trace-events', {
      params: { page: 1, pageSize: 10, eventType: 'INSPECTION', sortBy: 'eventTime', sortOrder: 'ASC' },
    })
  })
})
