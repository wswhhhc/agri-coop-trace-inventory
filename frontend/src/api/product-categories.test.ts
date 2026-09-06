import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { listProductCategories } from './product-categories'

vi.mock('./http', () => ({
  default: { get: vi.fn() },
}))

describe('product categories api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(http.get).mockResolvedValue({ data: { data: [] } })
  })

  it('requests the first page with category filters', async () => {
    await listProductCategories({ keyword: '蔬菜', isActive: true })

    expect(http.get).toHaveBeenCalledWith('/product-categories', {
      params: { page: 1, pageSize: 20, keyword: '蔬菜', isActive: true },
    })
  })

  it('returns the category list from the response body', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: { data: [{ id: 'category-1', code: 'VEG', name: '蔬菜', isActive: true }] },
    })

    await expect(listProductCategories()).resolves.toEqual([
      { id: 'category-1', code: 'VEG', name: '蔬菜', isActive: true },
    ])
  })
})
