import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { createProduct } from './products'

vi.mock('./http', () => ({
  default: { post: vi.fn() },
}))

describe('products api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
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
})
