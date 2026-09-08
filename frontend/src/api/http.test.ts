import { afterEach, describe, expect, it, vi } from 'vitest'
import { AxiosError, type InternalAxiosRequestConfig } from 'axios'

import http from './http'

function unauthorizedResponse(config: InternalAxiosRequestConfig) {
  return {
    status: 401,
    statusText: 'Unauthorized',
    headers: {},
    config,
    data: {
      error: {
        code: 'INVALID_CREDENTIALS',
        message: '用户名或密码错误',
      },
    },
  }
}

describe('http authentication interceptor', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('does not replace a login error with a refresh-token error', async () => {
    const adapter = vi.fn(async (config: InternalAxiosRequestConfig) => {
      throw new AxiosError(
        'Request failed with status code 401',
        'ERR_BAD_REQUEST',
        config,
        undefined,
        unauthorizedResponse(config),
      )
    })
    vi.spyOn(http.defaults, 'adapter', 'get').mockReturnValue(adapter)

    await expect(
      http.post('/auth/login', { username: 'wrong', password: 'wrong' }),
    ).rejects.toMatchObject({
      response: {
        data: {
          error: {
            message: '用户名或密码错误',
          },
        },
      },
    })

    expect(adapter).toHaveBeenCalledOnce()
    expect(adapter.mock.calls[0][0].url).toBe('/auth/login')
  })
})
