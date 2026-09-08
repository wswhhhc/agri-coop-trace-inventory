<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import FilterBar from '@/components/common/FilterBar.vue'
import { listCooperatives } from '@/api/cooperatives'
import { listWarehouses } from '@/api/warehouses'
import {
  createUser,
  listUsersPage,
  replaceUserWarehouses,
  resetUserPassword,
  updateUser,
} from '@/api/users'
import type { UserListParams, UserStatus } from '@/api/users'
import CreateFormModal from '@/components/common/CreateFormModal.vue'
import PageState from '@/components/common/PageState.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import SelectField, { type SelectFieldOption } from '@/components/common/SelectField.vue'
import { useFilteredPaginatedList, usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

type UserFilterState = Pick<UserListParams, 'keyword' | 'role' | 'status'> & {
  keyword: string
  role: string
  status: UserStatus | ''
}

const userList = useFilteredPaginatedList(
  (params) => listUsersPage({
    ...params,
    keyword: params.keyword || undefined,
    role: params.role || undefined,
    status: params.status || undefined,
  }),
  { keyword: '', role: '', status: '' } satisfies UserFilterState,
)
const authStore = useAuthStore()
const canManage = computed(() => authStore.hasPermission('user:manage'))
const showCooperativeSelector = computed(() => authStore.role === 'SYSTEM_ADMIN')
const availableRoles = computed(() =>
  authStore.role === 'COOPERATIVE_ADMIN'
    ? ['WAREHOUSE_STAFF']
    : ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
)
const filterRoleOptions = computed<SelectFieldOption[]>(() => [
  { value: '', label: '全部角色' },
  ...availableRoles.value.map((role) => ({ value: role, label: role })),
])
const userStatusOptions: SelectFieldOption[] = [
  { value: '', label: '全部状态' },
  { value: 'ACTIVE', label: '启用' },
  { value: 'LOCKED', label: '锁定' },
  { value: 'INACTIVE', label: '停用' },
]
const cooperativeState = usePageData(
  () => (showCooperativeSelector.value ? listCooperatives() : Promise.resolve([])),
  [],
)
const warehouseState = usePageData(listWarehouses, [])
const showCreateModal = ref(false)
const submitting = ref(false)
const updating = ref(false)
const authorizing = ref(false)
const resetting = ref(false)
const formError = ref('')
const successMessage = ref('')
const authorizationError = ref('')
const resetCredential = ref('')
const createdCredentials = ref('')
const editingUserId = ref<string | null>(null)
const form = reactive({
  username: '',
  displayName: '',
  role: 'WAREHOUSE_STAFF',
  cooperativeId: '',
  phone: '',
})
const editForm = reactive<{
  displayName: string
  role: string
  status: UserStatus
  phone: string
  warehouseIds: string[]
}>({
  displayName: '',
  role: 'WAREHOUSE_STAFF',
  status: 'ACTIVE',
  phone: '',
  warehouseIds: [],
})

const canAuthorize = computed(() => authStore.role === 'COOPERATIVE_ADMIN')

function resetForm(): void {
  form.username = ''
  form.displayName = ''
  form.role = availableRoles.value[0] ?? 'WAREHOUSE_STAFF'
  form.cooperativeId = ''
  form.phone = ''
}

function openCreateModal(): void {
  resetForm()
  formError.value = ''
  successMessage.value = ''
  createdCredentials.value = ''
  showCreateModal.value = true
}

function closeCreateModal(): void {
  if (submitting.value) return
  showCreateModal.value = false
  formError.value = ''
}

async function handleSubmit(): Promise<void> {
  if (showCooperativeSelector.value && form.role !== 'SYSTEM_ADMIN' && !form.cooperativeId) {
    formError.value = '非系统管理员用户必须选择合作社。'
    return
  }
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  createdCredentials.value = ''
  try {
    const result = await createUser({
      username: form.username.trim().toLowerCase(),
      displayName: form.displayName.trim(),
      role: form.role,
      cooperativeId: form.cooperativeId || null,
      warehouseIds: [],
      phone: form.phone.trim() || null,
    })
    resetForm()
    createdCredentials.value = `用户名：${result.username}；初始密码：${result.initialPassword}`
    successMessage.value = '用户创建成功，请安全传递初始密码。'
    await userList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

function beginEdit(user: (typeof userList.items)[number]): void {
  editingUserId.value = user.id
  editForm.displayName = user.displayName
  editForm.role = user.role
  editForm.status = user.status === 'LOCKED' ? 'LOCKED' : user.status === 'INACTIVE' ? 'INACTIVE' : 'ACTIVE'
  editForm.phone = user.phone ?? ''
  editForm.warehouseIds = [...user.warehouseIds]
  formError.value = ''
  authorizationError.value = ''
  resetCredential.value = ''
  successMessage.value = ''
  createdCredentials.value = ''
}

function cancelEdit(): void {
  editingUserId.value = null
  formError.value = ''
  authorizationError.value = ''
}

async function handleUpdate(): Promise<void> {
  if (!editingUserId.value) return
  updating.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    await updateUser(editingUserId.value, {
      displayName: editForm.displayName.trim(),
      role: editForm.role,
      status: editForm.status,
      phone: editForm.phone.trim() || null,
    })
    cancelEdit()
    successMessage.value = '用户更新成功。'
    await userList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    updating.value = false
  }
}

async function handleWarehouseAuthorization(): Promise<void> {
  if (!editingUserId.value || editForm.role !== 'WAREHOUSE_STAFF') return
  authorizing.value = true
  authorizationError.value = ''
  try {
    await replaceUserWarehouses(editingUserId.value, {
      warehouseIds: editForm.warehouseIds,
    })
    successMessage.value = '仓库授权更新成功。'
    await userList.loadData()
  } catch (reason) {
    authorizationError.value = getApiErrorMessage(reason)
  } finally {
    authorizing.value = false
  }
}

async function handleResetPassword(): Promise<void> {
  if (!editingUserId.value || !window.confirm('确定重置该用户密码吗？')) return
  resetting.value = true
  formError.value = ''
  resetCredential.value = ''
  try {
    const result = await resetUserPassword(editingUserId.value)
    resetCredential.value = `新的临时密码：${result.temporaryPassword}`
    successMessage.value = '密码重置成功，请安全传递临时密码。'
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    resetting.value = false
  }
}
</script>

<template>
  <section class="user-list-page">
    <div class="page-toolbar">
      <button v-if="canManage" class="create-button" type="button" @click="openCreateModal">创建用户</button>
    </div>
    <FilterBar @submit="userList.applyFilters" @reset="userList.resetFilters">
      <label>
        关键字
        <input v-model="userList.filters.keyword" placeholder="用户名或姓名" />
      </label>
      <label>
        角色
        <SelectField v-model="userList.filters.role" :options="filterRoleOptions" />
      </label>
      <label>
        状态
        <SelectField v-model="userList.filters.status" :options="userStatusOptions" />
      </label>
    </FilterBar>

    <CreateFormModal
      :open="showCreateModal"
      title="创建用户"
      :submitting="submitting"
      :error="formError"
      @close="closeCreateModal"
      @submit="handleSubmit"
    >
      <label>
        用户名
        <input
          v-model="form.username"
          name="username"
          required
          minlength="3"
          maxlength="50"
          pattern="[a-z0-9][a-z0-9_.-]{2,49}"
        />
      </label>
      <label>
        姓名
        <input v-model="form.displayName" name="displayName" required maxlength="50" />
      </label>
      <label>
        角色
        <select v-model="form.role">
          <option v-for="role in availableRoles" :key="role" :value="role">{{ role }}</option>
        </select>
      </label>
      <label v-if="showCooperativeSelector">
        合作社
        <select v-model="form.cooperativeId" :required="form.role !== 'SYSTEM_ADMIN'">
          <option value="">{{ form.role === 'SYSTEM_ADMIN' ? '不关联合作社' : '请选择合作社' }}</option>
          <option v-for="cooperative in cooperativeState.data" :key="cooperative.id" :value="cooperative.id">
            {{ cooperative.name }}
          </option>
        </select>
      </label>
      <label>
        联系电话
        <input
          v-model="form.phone"
          name="phone"
          inputmode="numeric"
          pattern="1[3-9][0-9]{9}"
          maxlength="11"
        />
      </label>
      <template #status>
        <p v-if="successMessage" class="user-create-status" role="status">{{ successMessage }}</p>
        <p v-if="createdCredentials" class="user-create-status" role="status">{{ createdCredentials }}</p>
      </template>
    </CreateFormModal>

    <form v-if="canManage && editingUserId" class="user-edit-form" @submit.prevent="handleUpdate">
      <h2>编辑用户</h2>
      <label>
        姓名
        <input v-model="editForm.displayName" name="edit-display-name" required maxlength="50" />
      </label>
      <label>
        角色
        <select v-model="editForm.role">
          <option v-for="role in availableRoles" :key="role" :value="role">{{ role }}</option>
        </select>
      </label>
      <label>
        状态
        <select v-model="editForm.status">
          <option value="ACTIVE">启用</option>
          <option value="LOCKED">锁定</option>
          <option value="INACTIVE">停用</option>
        </select>
      </label>
      <label>
        联系电话
        <input
          v-model="editForm.phone"
          name="edit-phone"
          inputmode="numeric"
          pattern="1[3-9][0-9]{9}"
          maxlength="11"
        />
      </label>
      <label v-if="canAuthorize && editForm.role === 'WAREHOUSE_STAFF'">
        授权仓库
        <select v-model="editForm.warehouseIds" multiple size="5">
          <option v-for="warehouse in warehouseState.data" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}（{{ warehouse.code }}）
          </option>
        </select>
      </label>
      <button type="submit" :disabled="updating">{{ updating ? '保存中…' : '保存' }}</button>
      <button type="button" :disabled="updating" @click="cancelEdit">取消</button>
      <button
        v-if="canAuthorize && editForm.role === 'WAREHOUSE_STAFF'"
        type="button"
        :disabled="authorizing"
        @click="handleWarehouseAuthorization"
      >
        {{ authorizing ? '授权中…' : '保存仓库授权' }}
      </button>
      <button type="button" :disabled="resetting" @click="handleResetPassword">
        {{ resetting ? '重置中…' : '重置密码' }}
      </button>
      <p v-if="authorizationError" role="alert">{{ authorizationError }}</p>
      <p v-if="resetCredential" role="status">{{ resetCredential }}</p>
    </form>

    <PageState
      :loading="userList.loading"
      :error="userList.error"
      :empty="userList.items.length === 0"
      @retry="userList.loadData"
    >
      <table>
        <caption>用户列表</caption>
        <thead>
          <tr>
            <th scope="col">用户名</th>
            <th scope="col">姓名</th>
            <th scope="col">角色</th>
            <th scope="col">联系电话</th>
            <th scope="col">状态</th>
            <th v-if="canManage" scope="col">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in userList.items" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.displayName }}</td>
            <td>{{ user.role }}</td>
            <td>{{ user.phone || '—' }}</td>
            <td><StatusBadge :label="user.status" :tone="user.status === 'ACTIVE' ? 'success' : user.status === 'LOCKED' ? 'danger' : 'neutral'" /></td>
            <td v-if="canManage">
              <button type="button" @click="beginEdit(user)">编辑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </PageState>
    <PaginationBar
      :page="userList.pagination.page"
      :total-pages="userList.pagination.totalPages"
      :total-items="userList.pagination.totalItems"
      :page-size="userList.pagination.pageSize"
      @change="userList.goToPage"
      @page-size-change="userList.setPageSize"
    />
  </section>
</template>

<style scoped>
.user-list-page {
  display: grid;
  gap: var(--space-5);
}

.page-toolbar {
  display: flex;
  justify-content: flex-end;
}

.create-button {
  min-height: 2.5rem;
  padding: var(--space-2) var(--space-4);
}

.user-list-page > .page-state {
  overflow-x: auto;
}

.user-list-page > .page-state table {
  min-width: 64rem;
}

.user-edit-form {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.user-edit-form h2 {
  grid-column: 1 / -1;
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.user-edit-form > label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.user-edit-form > p {
  grid-column: 1 / -1;
  margin: 0;
  font-size: var(--font-size-sm);
}

.user-edit-form > p[role='alert'] {
  color: var(--color-danger);
}

.user-edit-form > p[role='status'] {
  color: var(--color-success);
}

.user-edit-form > button {
  justify-self: start;
}

@media (max-width: 48rem) {
  .user-edit-form {
    grid-template-columns: 1fr;
    padding: var(--space-4);
  }

  .user-edit-form h2,
  .user-edit-form > p {
    grid-column: auto;
  }

  .user-edit-form > button {
    justify-self: stretch;
  }
}

.user-create-status {
  margin: 0;
  color: var(--color-success);
  font-size: var(--font-size-sm);
}
</style>
