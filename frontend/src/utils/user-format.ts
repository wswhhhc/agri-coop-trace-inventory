const userStatusLabels: Record<string, string> = {
  ACTIVE: '启用',
  LOCKED: '锁定',
  INACTIVE: '停用',
}

export function formatUserStatus(status: string): string {
  return userStatusLabels[status] ?? status
}
