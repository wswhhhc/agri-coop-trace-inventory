<script setup lang="ts">
import { computed, ref } from 'vue'

import { listPermissions, listRolesPage, updateRolePermissions } from '@/api/roles'
import PageState from '@/components/common/PageState.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import { usePageData, usePaginatedList } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const authStore = useAuthStore()
const canManage = computed(() => authStore.role === 'SYSTEM_ADMIN')
const roleList = usePaginatedList(listRolesPage)
const permissionState = usePageData(listPermissions, [])
const editingRoleId = ref<string | null>(null)
const selectedPermissionCodes = ref<string[]>([])
const submitting = ref(false)
const formError = ref('')
const successMessage = ref('')

function beginEdit(role: (typeof roleList.items)[number]): void {
  editingRoleId.value = role.id
  selectedPermissionCodes.value = role.permissions.map((permission) => permission.code)
  formError.value = ''
  successMessage.value = ''
}

function cancelEdit(): void {
  editingRoleId.value = null
  formError.value = ''
}

async function handleUpdate(): Promise<void> {
  if (!editingRoleId.value) return
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    await updateRolePermissions(editingRoleId.value, selectedPermissionCodes.value)
    cancelEdit()
    successMessage.value = '角色权限更新成功。'
    await roleList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

async function loadData(): Promise<void> {
  await Promise.all([roleList.loadData(), permissionState.loadData()])
}
</script>

<template>
  <section class="role-list-page">
    <PageState
      :loading="roleList.loading || permissionState.loading"
      :error="roleList.error || permissionState.error"
      :empty="roleList.items.length === 0"
      empty-message="暂无角色数据"
      @retry="loadData"
    >
      <p v-if="!canManage" role="alert">只有系统管理员可以维护角色权限。</p>
      <p v-if="formError" role="alert">{{ formError }}</p>
      <p v-if="successMessage" role="status">{{ successMessage }}</p>
      <table>
        <caption>角色列表</caption>
        <thead>
          <tr>
            <th scope="col">编码</th>
            <th scope="col">名称</th>
            <th scope="col">说明</th>
            <th scope="col">权限</th>
            <th v-if="canManage" scope="col">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="role in roleList.items" :key="role.id">
            <td>{{ role.code }}</td>
            <td>{{ role.name }}</td>
            <td>{{ role.description || '—' }}</td>
            <td>{{ role.permissions.map((permission) => permission.code).join('、') || '无' }}</td>
            <td v-if="canManage">
              <button type="button" @click="beginEdit(role)">编辑权限</button>
            </td>
          </tr>
        </tbody>
      </table>
    </PageState>
    <PaginationBar
      :page="roleList.pagination.page"
      :total-pages="roleList.pagination.totalPages"
      :total-items="roleList.pagination.totalItems"
      :page-size="roleList.pagination.pageSize"
      @change="roleList.goToPage"
      @page-size-change="roleList.setPageSize"
    />

    <form v-if="canManage && editingRoleId" class="role-permission-edit-form" @submit.prevent="handleUpdate">
      <h2>编辑角色权限</h2>
      <label v-for="permission in permissionState.data" :key="permission.id">
        <input v-model="selectedPermissionCodes" type="checkbox" :value="permission.code" />
        {{ permission.name }}（{{ permission.code }}）
      </label>
      <button type="submit" :disabled="submitting">{{ submitting ? '保存中…' : '保存' }}</button>
      <button type="button" :disabled="submitting" @click="cancelEdit">取消</button>
    </form>
  </section>
</template>

<style scoped>
.role-list-page {
  display: grid;
  gap: var(--space-5);
}

.role-list-page > .page-state {
  overflow-x: auto;
}

.role-list-page > .page-state table {
  min-width: 56rem;
}

.role-list-page > .page-state > p[role='alert'],
.role-list-page > .page-state > p[role='status'] {
  margin: 0 0 var(--space-4);
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
}

.role-list-page > .page-state > p[role='alert'] {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.role-list-page > .page-state > p[role='status'] {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.role-permission-edit-form {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.role-permission-edit-form h2 {
  grid-column: 1 / -1;
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.role-permission-edit-form > label {
  display: flex;
  min-height: 3.25rem;
  align-items: center;
  gap: var(--space-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  background: var(--color-surface-muted);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.role-permission-edit-form > button {
  justify-self: start;
}

@media (max-width: 48rem) {
  .role-permission-edit-form {
    grid-template-columns: 1fr;
    padding: var(--space-4);
  }

  .role-permission-edit-form h2 {
    grid-column: auto;
  }

  .role-permission-edit-form > button {
    justify-self: stretch;
  }
}
</style>
