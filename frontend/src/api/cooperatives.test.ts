import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { createCooperative, listCooperatives, updateCooperative } from './cooperatives'

vi.mock('./http', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}))

describe('cooperatives api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('lists cooperatives with pagination', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [] } })

    await expect(listCooperatives()).resolves.toEqual([])
    expect(http.get).toHaveBeenCalledWith('/cooperatives', {
      params: { page: 1, pageSize: 20 },
    })
  })

  it('creates a cooperative', async () => {
    const payload = {
      code: 'COOP-01',
      name: '示范合作社',
      address: '农业路 1 号',
      contactName: '张三',
      contactPhone: '13800138000',
    }
    vi.mocked(http.post).mockResolvedValueOnce({ data: { data: { id: 'cooperative-1', ...payload, status: 'ACTIVE' } } })

    await expect(createCooperative(payload)).resolves.toMatchObject({ id: 'cooperative-1' })
    expect(http.post).toHaveBeenCalledWith('/cooperatives', payload)
  })

  it('updates cooperative details and status', async () => {
    const payload = {
      name: '示范合作社（停用）',
      address: null,
      contactName: '李四',
      contactPhone: null,
      status: 'INACTIVE' as const,
    }
    vi.mocked(http.patch).mockResolvedValueOnce({ data: { data: { id: 'cooperative-1', ...payload } } })

    await expect(updateCooperative('cooperative-1', payload)).resolves.toMatchObject({
      id: 'cooperative-1',
      status: 'INACTIVE',
    })
    expect(http.patch).toHaveBeenCalledWith('/cooperatives/cooperative-1', payload)
  })
})
