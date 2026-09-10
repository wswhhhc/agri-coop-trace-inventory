import type { UserRole } from '@/types/auth'
import { hasRequiredAccess, type AccessSubject } from '@/utils/permission'

export interface MenuItem {
  title: string
  path: string
  roles?: UserRole[]
  permissions?: string[]
  children?: MenuItem[]
}

export const menuItems: MenuItem[] = [
  {
    title: '首页',
    path: '/dashboard',
    roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
    permissions: ['inventory:read'],
  },
  {
    title: '智能查询',
    path: '/assistant',
    roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
  },
  {
    title: '合作社管理',
    path: '/cooperatives',
    roles: ['SYSTEM_ADMIN'],
    permissions: ['cooperative:manage'],
  },
  {
    title: '用户管理',
    path: '/users',
    roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN'],
    permissions: ['user:manage'],
  },
  { title: '角色与权限', path: '/roles', roles: ['SYSTEM_ADMIN'] },
  {
    title: '仓库管理',
    path: '/warehouses',
    roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
  },
  {
    title: '产品管理',
    path: '/products',
    roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
  },
  {
    title: '产品分类',
    path: '/product-categories',
    roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
  },
  {
    title: '批次管理',
    path: '/batches',
    roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
  },
  {
    title: '库存管理',
    path: '/inventory',
    roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
    permissions: ['inventory:read'],
  },
  {
    title: '库存流水',
    path: '/inventory-transactions',
    roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
    permissions: ['inventory:read'],
  },
  {
    title: '预警中心',
    path: '/alerts',
    roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
    permissions: ['alert:read'],
  },
  {
    title: 'AI 预测',
    path: '/forecasting',
    roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
    permissions: ['model:read'],
  },
  {
    title: '操作日志',
    path: '/audit-logs',
    roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
    permissions: ['audit:read'],
  },
  {
    title: '报表导出',
    path: '/export',
    roles: ['COOPERATIVE_ADMIN'],
  },
]

export function filterMenuItems(items: MenuItem[], subject: AccessSubject): MenuItem[] {
  return items.flatMap((item) => {
    const children = item.children ? filterMenuItems(item.children, subject) : undefined
    const canAccess = hasRequiredAccess(subject, item)
    if (!canAccess && !children?.length) return []

    return [{ ...item, ...(children ? { children } : {}) }]
  })
}
