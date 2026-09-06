import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { uploadFile } from './files'

vi.mock('./http', () => ({
  default: { post: vi.fn() },
}))

describe('files api', () => {
  beforeEach(() => vi.clearAllMocks())

  it('uploads a file as multipart form data', async () => {
    const file = new File(['report'], 'report.pdf', { type: 'application/pdf' })
    const uploaded = { id: 'file-1', originalName: 'report.pdf' }
    vi.mocked(http.post).mockResolvedValueOnce({ data: { data: uploaded } })

    await expect(uploadFile(file)).resolves.toEqual(uploaded)
    expect(http.post).toHaveBeenCalledWith('/files', expect.any(FormData))
    const body = vi.mocked(http.post).mock.calls[0][1] as FormData
    expect(body.get('upload')).toBe(file)
  })
})
