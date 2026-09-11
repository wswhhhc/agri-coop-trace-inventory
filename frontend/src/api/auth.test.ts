import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { changePassword } from './auth'

vi.mock('./http', () => ({
  default: { post: vi.fn() },
}))

describe('auth api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('changes the current user password', async () => {
    const payload = {
      currentPassword: 'old-password',
      newPassword: 'new-password-123',
    }
    vi.mocked(http.post).mockResolvedValueOnce({ data: undefined })

    await expect(changePassword(payload)).resolves.toBeUndefined()
    expect(http.post).toHaveBeenCalledWith('/auth/password', payload)
  })
})
