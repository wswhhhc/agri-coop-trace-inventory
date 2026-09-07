import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

import { clearAccessToken, getAccessToken, setAccessToken } from './session'
import type { ApiErrorBody, ApiResponse } from '@/types/api'
import type { AuthTokenData } from '@/types/auth'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  timeout: 15000,
  withCredentials: true,
  headers: {
    Accept: 'application/json',
  },
})

let refreshPromise: Promise<string> | null = null

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const originalRequest = error.config
    const isRefreshRequest = originalRequest?.url?.endsWith('/auth/refresh')

    if (error.response?.status !== 401 || !originalRequest || isRefreshRequest) {
      return Promise.reject(error)
    }

    if (!refreshPromise) {
      refreshPromise = http
        .post<ApiResponse<AuthTokenData>>('/auth/refresh')
        .then((response) => {
          const token = response.data.data.accessToken
          setAccessToken(token)
          return token
        })
        .finally(() => {
          refreshPromise = null
        })
    }

    try {
      const token = await refreshPromise
      originalRequest.headers.Authorization = `Bearer ${token}`
      return http(originalRequest)
    } catch (refreshError) {
      clearAccessToken()
      return Promise.reject(refreshError)
    }
  },
)

export default http
