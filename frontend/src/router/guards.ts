import type { RouteLocationRaw, RouteMeta } from 'vue-router'

import type { UserRole } from '@/types/auth'
import { hasRequiredAccess } from '@/utils/permission'

export interface GuardRoute {
  fullPath: string
  meta: Pick<RouteMeta, 'requiresAuth' | 'guestOnly' | 'roles' | 'permissions'>
}

export interface GuardAuthState {
  isAuthenticated: boolean
  role: UserRole | null
  permissions: readonly string[]
}

export function resolveRouteAccess(
  to: GuardRoute,
  auth: GuardAuthState,
): RouteLocationRaw | true {
  const hasRestrictions = Boolean(to.meta.roles?.length || to.meta.permissions?.length)

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }

  if (
    hasRestrictions &&
    (!auth.isAuthenticated ||
      !hasRequiredAccess(
        auth.role ? { role: auth.role, permissions: auth.permissions } : null,
        to.meta,
      ))
  ) {
    return { name: 'forbidden' }
  }

  return true
}
