import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { listAlertRules, updateAlertRule } from './alerts'

vi.mock('./http', () => ({
  default: { get: vi.fn(), patch: vi.fn() },
}))

describe('alerts api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('lists alert rules', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [] } })

    await expect(listAlertRules()).resolves.toEqual([])
    expect(http.get).toHaveBeenCalledWith('/alert-rules', {
      params: { page: 1, pageSize: 100 },
    })
  })

  it('updates an alert rule', async () => {
    const payload = { thresholdQuantity: 20, severity: 'HIGH', isEnabled: true }
    vi.mocked(http.patch).mockResolvedValueOnce({
      data: { data: { id: 'rule-1', ...payload } },
    })

    await expect(updateAlertRule('rule-1', payload)).resolves.toMatchObject({
      id: 'rule-1',
      severity: 'HIGH',
    })
    expect(http.patch).toHaveBeenCalledWith('/alert-rules/rule-1', payload)
  })
})
