import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { createQualityInspection, listQualityInspections } from './quality-inspections'

vi.mock('./http', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

describe('quality inspections api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('lists inspections for a batch', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [] } })

    await expect(listQualityInspections('batch-1')).resolves.toEqual([])
    expect(http.get).toHaveBeenCalledWith('/batches/batch-1/quality-inspections', {
      params: { page: 1, pageSize: 20 },
    })
  })

  it('creates an inspection with item results', async () => {
    const payload = {
      inspectionDate: '2026-09-06',
      conclusion: 'PASSED' as const,
      items: [
        { name: '农残', value: '合格', unit: null, standard: '不得检出', isQualified: true },
      ],
      remarks: '抽检通过',
    }
    vi.mocked(http.post).mockResolvedValueOnce({
      data: { data: { id: 'inspection-1', inspectionNo: 'QC-001', conclusion: 'PASSED' } },
    })

    await expect(createQualityInspection('batch-1', payload)).resolves.toMatchObject({
      id: 'inspection-1',
      conclusion: 'PASSED',
    })
    expect(http.post).toHaveBeenCalledWith('/batches/batch-1/quality-inspections', payload)
  })
})
