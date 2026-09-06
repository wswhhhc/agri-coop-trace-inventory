import type { ApiResponse, ListResponse } from '@/types/api'
import type { PermissionSummary, RoleSummary } from '@/types/resources'

import http from './http'

export async function listRoles(): Promise<RoleSummary[]> {
  const response = await http.get<ListResponse<RoleSummary>>('/roles', {
    params: { page: 1, pageSize: 100 },
  })
  return response.data.data
}

export async function listPermissions(): Promise<PermissionSummary[]> {
  const response = await http.get<ListResponse<PermissionSummary>>('/roles/permissions', {
    params: { page: 1, pageSize: 100 },
  })
  return response.data.data
}

export async function updateRolePermissions(
  roleId: string,
  permissionCodes: string[],
): Promise<RoleSummary> {
  const response = await http.put<ApiResponse<RoleSummary>>(`/roles/${roleId}/permissions`, {
    permissionCodes,
  })
  return response.data.data
}
