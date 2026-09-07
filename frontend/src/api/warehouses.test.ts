import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { createWarehouse, listWarehouses, updateWarehouse } from './warehouses'

vi.mock('./http', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}))

describe('warehouses api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('lists warehouses with pagination', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [] } })

    await expect(listWarehouses()).resolves.toEqual([])
    expect(http.get).toHaveBeenCalledWith('/warehouses', {
      params: { page: 1, pageSize: 20 },
    })
  })

  it('creates a warehouse', async () => {
    const payload = {
      cooperativeId: 'cooperative-1',
      name: '中心仓',
      address: '农业路 1 号',
      managerName: '张三',
    }
    vi.mocked(http.post).mockResolvedValueOnce({
      data: { data: { id: 'warehouse-1', code: 'WH-ABC123', ...payload, status: 'ACTIVE' } },
    })

    await expect(createWarehouse(payload)).resolves.toMatchObject({ id: 'warehouse-1' })
    expect(http.post).toHaveBeenCalledWith('/warehouses', payload)
  })

  it('updates warehouse details and status', async () => {
    const payload = {
      name: '冷链仓',
      address: null,
      managerName: '李四',
      status: 'INACTIVE' as const,
    }
    vi.mocked(http.patch).mockResolvedValueOnce({ data: { data: { id: 'warehouse-1', ...payload } } })

    await expect(updateWarehouse('warehouse-1', payload)).resolves.toMatchObject({
      id: 'warehouse-1',
      status: 'INACTIVE',
    })
    expect(http.patch).toHaveBeenCalledWith('/warehouses/warehouse-1', payload)
  })
})
