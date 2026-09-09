const userRoleLabels: Record<string, string> = {
  SYSTEM_ADMIN: '系统管理员',
  COOPERATIVE_ADMIN: '合作社管理员',
  WAREHOUSE_STAFF: '仓库工作人员',
}

const userStatusLabels: Record<string, string> = {
  ACTIVE: '启用',
  LOCKED: '锁定',
  INACTIVE: '停用',
}

export function formatUserRole(role: string): string {
  return userRoleLabels[role] ?? role
}

export function formatUserStatus(status: string): string {
  return userStatusLabels[status] ?? status
}
