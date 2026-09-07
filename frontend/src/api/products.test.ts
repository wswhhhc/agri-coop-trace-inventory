import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { createProduct, listProducts, updateProduct } from './products'

vi.mock('./http', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}))

describe('products api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads only active products with a large enough page size for selectors', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [] } })

    await expect(listProducts({ isActive: true, pageSize: 100 })).resolves.toEqual([])
    expect(http.get).toHaveBeenCalledWith('/products', {
      params: { page: 1, pageSize: 100, isActive: true },
    })
  })

  it('creates a product with the product contract', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: {
        data: {
          id: 'product-1',
          code: 'APPLE',
          name: '苹果',
          categoryId: 'category-1',
          unit: 'KG',
          shelfLifeDays: 30,
          safetyStock: 10,
          isActive: true,
        },
      },
    })

    const payload = {
      categoryId: 'category-1',
      code: 'APPLE',
      name: '苹果',
      unit: 'KG' as const,
      shelfLifeDays: 30,
      safetyStock: 10,
    }

    await expect(createProduct(payload)).resolves.toEqual({
      id: 'product-1',
      code: 'APPLE',
      name: '苹果',
      categoryId: 'category-1',
      unit: 'KG',
      shelfLifeDays: 30,
      safetyStock: 10,
      isActive: true,
    })
    expect(http.post).toHaveBeenCalledWith('/products', payload)
  })

  it('updates a product and returns the updated resource', async () => {
    vi.mocked(http.patch).mockResolvedValueOnce({
      data: {
        data: {
          id: 'product-1',
          code: 'APPLE',
          name: '精品苹果',
          categoryId: 'category-1',
          unit: 'BOX',
          shelfLifeDays: 20,
          safetyStock: 12,
          isActive: false,
        },
      },
    })

    const payload = {
      name: '精品苹果',
      unit: 'BOX' as const,
      shelfLifeDays: 20,
      safetyStock: 12,
      isActive: false,
    }

    await expect(updateProduct('product-1', payload)).resolves.toEqual({
      id: 'product-1',
      code: 'APPLE',
      name: '精品苹果',
      categoryId: 'category-1',
      unit: 'BOX',
      shelfLifeDays: 20,
      safetyStock: 12,
      isActive: false,
    })
    expect(http.patch).toHaveBeenCalledWith('/products/product-1', payload)
  })
})
