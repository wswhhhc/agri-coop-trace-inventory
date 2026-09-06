import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { getAlert, listAlertRules, updateAlert, updateAlertRule } from './alerts'

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

  it('gets alert detail', async () => {
    const detail = {
      id: 'alert-1',
      alertType: 'LOW_STOCK',
      severity: 'HIGH',
      status: 'PENDING',
      title: '库存不足',
      message: '库存低于安全库存',
      detectedAt: '2026-09-06T10:00:00.000Z',
      ruleId: 'rule-1',
      warehouseId: 'warehouse-1',
      productId: 'product-1',
      batchId: null,
      evidence: { availableQuantity: 3 },
      resolvedAt: null,
      assigneeId: null,
      handlingLogs: [],
    }
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: detail } })

    await expect(getAlert('alert-1')).resolves.toEqual(detail)
    expect(http.get).toHaveBeenCalledWith('/alerts/alert-1')
  })

  it('updates alert status with a handling note', async () => {
    const payload = { status: 'RESOLVED', handlingNote: '已补充库存' }
    vi.mocked(http.patch).mockResolvedValueOnce({
      data: { data: { id: 'alert-1', status: 'RESOLVED' } },
    })

    await expect(updateAlert('alert-1', payload)).resolves.toMatchObject({
      id: 'alert-1',
      status: 'RESOLVED',
    })
    expect(http.patch).toHaveBeenCalledWith('/alerts/alert-1', payload)
  })
})
