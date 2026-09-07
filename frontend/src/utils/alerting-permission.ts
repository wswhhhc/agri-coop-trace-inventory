import type { UserRole } from '@/types/auth'

export function canManageAlertRules(
  role: UserRole | null,
  permissions: readonly string[],
): boolean {
  return role === 'COOPERATIVE_ADMIN' && permissions.includes('alert:read')
}
