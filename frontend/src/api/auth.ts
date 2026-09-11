import http from './http'
import type { ApiResponse } from '@/types/api'
import type { AuthTokenData, CurrentUser, LoginRequest } from '@/types/auth'

export interface ChangePasswordPayload {
  currentPassword: string
  newPassword: string
}

export async function login(payload: LoginRequest) {
  const response = await http.post<ApiResponse<AuthTokenData>>('/auth/login', payload)
  return response.data.data
}

export async function refresh() {
  const response = await http.post<ApiResponse<AuthTokenData>>('/auth/refresh')
  return response.data.data
}

export async function getCurrentUser() {
  const response = await http.get<ApiResponse<CurrentUser>>('/auth/me')
  return response.data.data
}

export async function logout() {
  await http.post('/auth/logout')
}

export async function changePassword(payload: ChangePasswordPayload): Promise<void> {
  await http.post('/auth/password', payload)
}
