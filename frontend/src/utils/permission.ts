import type { UserRole } from '@/types/auth'

export interface AccessSubject {
  role: UserRole
  permissions: readonly string[]
}

export interface AccessRequirements {
  roles?: readonly UserRole[]
  permissions?: readonly string[]
}

export function hasRole(subject: AccessSubject, role: UserRole): boolean {
  return subject.role === role
}

export function hasPermission(subject: AccessSubject, permission: string): boolean {
  return subject.permissions.includes(permission)
}

export function hasRequiredAccess(
  subject: AccessSubject | null | undefined,
  requirements: AccessRequirements,
): boolean {
  if (!subject) return false

  const roleAllowed = !requirements.roles?.length || requirements.roles.includes(subject.role)
  const permissionsAllowed =
    !requirements.permissions?.length ||
    requirements.permissions.every((permission) => hasPermission(subject, permission))

  return roleAllowed && permissionsAllowed
}
