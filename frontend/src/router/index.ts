import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

import './types'
import { resolveRouteAccess } from './guards'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guestOnly: true, title: '登录' },
    },
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      redirect: { name: 'dashboard' },
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
          meta: { requiresAuth: true, title: '首页', permissions: ['inventory:read'] },
        },
        {
          path: 'cooperatives',
          name: 'cooperatives',
          component: () => import('@/views/cooperatives/CooperativeListView.vue'),
          meta: {
            requiresAuth: true,
            title: '合作社管理',
            roles: ['SYSTEM_ADMIN'],
            permissions: ['cooperative:manage'],
          },
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/users/UserListView.vue'),
          meta: {
            requiresAuth: true,
            title: '用户管理',
            roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN'],
            permissions: ['user:manage'],
          },
        },
        {
          path: 'roles',
          name: 'roles',
          component: () => import('@/views/roles/RoleListView.vue'),
          meta: { requiresAuth: true, title: '角色与权限', roles: ['SYSTEM_ADMIN'] },
        },
        {
          path: 'warehouses',
          name: 'warehouses',
          component: () => import('@/views/warehouses/WarehouseListView.vue'),
          meta: {
            requiresAuth: true,
            title: '仓库管理',
            roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
          },
        },
        {
          path: 'products',
          name: 'products',
          component: () => import('@/views/products/ProductListView.vue'),
          meta: {
            requiresAuth: true,
            title: '产品管理',
            roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
          },
        },
        {
          path: 'batches',
          name: 'batches',
          component: () => import('@/views/batches/BatchListView.vue'),
          meta: {
            requiresAuth: true,
            title: '批次管理',
            roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
          },
        },
        {
          path: 'inventory',
          name: 'inventory',
          component: () => import('@/views/inventory/InventoryListView.vue'),
          meta: {
            requiresAuth: true,
            title: '库存管理',
            roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
            permissions: ['inventory:read'],
          },
        },
        {
          path: 'inventory-transactions',
          name: 'inventory-transactions',
          component: () => import('@/views/inventory/InventoryTransactionListView.vue'),
          meta: {
            requiresAuth: true,
            title: '库存流水',
            roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
            permissions: ['inventory:read'],
          },
        },
        {
          path: 'alerts',
          name: 'alerts',
          component: () => import('@/views/alerts/AlertListView.vue'),
          meta: {
            requiresAuth: true,
            title: '预警中心',
            roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
            permissions: ['alert:read'],
          },
        },
        {
          path: 'forecasting',
          name: 'forecasting',
          component: () => import('@/views/forecasting/ForecastingView.vue'),
          meta: {
            requiresAuth: true,
            title: 'AI 预测',
            roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
            permissions: ['model:read'],
          },
        },
        {
          path: 'audit-logs',
          name: 'audit-logs',
          component: () => import('@/views/audit-logs/AuditLogListView.vue'),
          meta: {
            requiresAuth: true,
            title: '操作日志',
            roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
            permissions: ['audit:read'],
          },
        },
        {
          path: '403',
          name: 'forbidden',
          component: () => import('@/views/error/ForbiddenView.vue'),
          meta: { requiresAuth: true, title: '无权限' },
        },
      ],
    },
    {
      path: '/404',
      name: 'not-found',
      component: () => import('@/views/error/NotFoundView.vue'),
      meta: { requiresAuth: true, title: '页面不存在' },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found-catch',
      redirect: { name: 'not-found' },
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  await authStore.initialize()

  return resolveRouteAccess(to, {
    isAuthenticated: authStore.isAuthenticated,
    role: authStore.role,
    permissions: authStore.permissions,
  })
})

export default router
