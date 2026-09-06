import type { ApiResponse, ListResponse } from '@/types/api'
import type { UserSummary } from '@/types/resources'

import http from './http'

export type UserStatus = 'ACTIVE' | 'LOCKED' | 'INACTIVE'

export interface UserCreatePayload {
  username: string
  displayName: string
  role: string
  cooperativeId: string | null
  warehouseIds: string[]
  phone: string | null
}

export interface UserUpdatePayload {
  displayName: string
  role: string
  status: UserStatus
  phone: string | null
}

export interface UserWarehouseAssignmentPayload {
  warehouseIds: string[]
}

export interface UserCreateResult extends UserSummary {
  initialPassword: string
}

export interface PasswordResetResult {
  temporaryPassword: string
}

export async function listUsers(): Promise<UserSummary[]> {
  const response = await http.get<ListResponse<UserSummary>>('/users', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}

export async function createUser(payload: UserCreatePayload): Promise<UserCreateResult> {
  const response = await http.post<ApiResponse<UserCreateResult>>('/users', payload)
  return response.data.data
}

export async function updateUser(
  userId: string,
  payload: UserUpdatePayload,
): Promise<UserSummary> {
  const response = await http.patch<ApiResponse<UserSummary>>(`/users/${userId}`, payload)
  return response.data.data
}

export async function replaceUserWarehouses(
  userId: string,
  payload: UserWarehouseAssignmentPayload,
): Promise<UserSummary> {
  const response = await http.put<ApiResponse<UserSummary>>(
    `/users/${userId}/warehouses`,
    payload,
  )
  return response.data.data
}

export async function resetUserPassword(userId: string): Promise<PasswordResetResult> {
  const response = await http.post<ApiResponse<PasswordResetResult>>(
    `/users/${userId}/password-resets`,
  )
  return response.data.data
}
