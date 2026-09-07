import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import {
  createProductCategory,
  listProductCategories,
  updateProductCategory,
} from './product-categories'

vi.mock('./http', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
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

  it('creates a category and returns the created resource', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: { data: { id: 'category-2', code: 'FRUIT', name: '水果', isActive: true } },
    })

    await expect(
      createProductCategory({ name: '水果', description: null }),
    ).resolves.toEqual({ id: 'category-2', code: 'FRUIT', name: '水果', isActive: true })

    expect(http.post).toHaveBeenCalledWith('/product-categories', {
      name: '水果',
      description: null,
    })
  })

  it('updates a category and returns the updated resource', async () => {
    vi.mocked(http.patch).mockResolvedValueOnce({
      data: { data: { id: 'category-1', code: 'VEG', name: '蔬菜类', isActive: false } },
    })

    await expect(
      updateProductCategory('category-1', {
        name: '蔬菜类',
        description: null,
        isActive: false,
      }),
    ).resolves.toEqual({ id: 'category-1', code: 'VEG', name: '蔬菜类', isActive: false })

    expect(http.patch).toHaveBeenCalledWith('/product-categories/category-1', {
      name: '蔬菜类',
      description: null,
      isActive: false,
    })
  })
})
