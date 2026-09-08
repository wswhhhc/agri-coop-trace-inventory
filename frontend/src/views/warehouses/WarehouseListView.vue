<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import FilterBar from '@/components/common/FilterBar.vue'
import { listCooperatives } from '@/api/cooperatives'
import {
  createWarehouse,
  listWarehousesPage,
  updateWarehouse,
} from '@/api/warehouses'
import type { WarehouseListParams, WarehouseStatus } from '@/api/warehouses'
import CreateFormModal from '@/components/common/CreateFormModal.vue'
import GeneratedCodeField from '@/components/common/GeneratedCodeField.vue'
import PageState from '@/components/common/PageState.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import SelectField, { type SelectFieldOption } from '@/components/common/SelectField.vue'
import { useFilteredPaginatedList, usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

type WarehouseFilterState = Pick<WarehouseListParams, 'keyword' | 'status'> & {
  keyword: string
  status: WarehouseStatus | ''
}

const warehouseList = useFilteredPaginatedList(
  (params) => listWarehousesPage({
    ...params,
    keyword: params.keyword || undefined,
    status: params.status || undefined,
  }),
  { keyword: '', status: '' } satisfies WarehouseFilterState,
)
const warehouseStatusOptions: SelectFieldOption[] = [
  { value: '', label: '全部状态' },
  { value: 'ACTIVE', label: '启用' },
  { value: 'INACTIVE', label: '停用' },
]
const authStore = useAuthStore()
const canManage = computed(() => authStore.hasPermission('warehouse:manage'))
const showCooperativeSelector = computed(() => authStore.role === 'SYSTEM_ADMIN')
const cooperativeState = usePageData(
  () => (showCooperativeSelector.value ? listCooperatives() : Promise.resolve([])),
  [],
)
const showCreateModal = ref(false)
const submitting = ref(false)
const updating = ref(false)
const formError = ref('')
const successMessage = ref('')
const editingWarehouseId = ref<string | null>(null)
const form = reactive({
  cooperativeId: '',
  name: '',
  address: '',
  managerName: '',
})
const editForm = reactive<{
  name: string
  address: string
  managerName: string
  status: WarehouseStatus
}>({
  name: '',
  address: '',
  managerName: '',
  status: 'ACTIVE',
})

function resetForm(): void {
  form.cooperativeId = ''
  form.name = ''
  form.address = ''
  form.managerName = ''
}

function openCreateModal(): void {
  resetForm()
  formError.value = ''
  successMessage.value = ''
  showCreateModal.value = true
}

function closeCreateModal(): void {
  if (submitting.value) return
  showCreateModal.value = false
  formError.value = ''
}

async function handleSubmit(): Promise<void> {
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    await createWarehouse({
      cooperativeId: form.cooperativeId || null,
      name: form.name.trim(),
      address: form.address.trim() || null,
      managerName: form.managerName.trim() || null,
    })
    resetForm()
    showCreateModal.value = false
    successMessage.value = '仓库创建成功。'
    await warehouseList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

function beginEdit(warehouse: (typeof warehouseList.items)[number]): void {
  editingWarehouseId.value = warehouse.id
  editForm.name = warehouse.name
  editForm.address = warehouse.address ?? ''
  editForm.managerName = warehouse.managerName ?? ''
  editForm.status = warehouse.status === 'INACTIVE' ? 'INACTIVE' : 'ACTIVE'
  formError.value = ''
  successMessage.value = ''
}

function cancelEdit(): void {
  editingWarehouseId.value = null
  formError.value = ''
}

async function handleUpdate(): Promise<void> {
  if (!editingWarehouseId.value) return
  updating.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    await updateWarehouse(editingWarehouseId.value, {
      name: editForm.name.trim(),
      address: editForm.address.trim() || null,
      managerName: editForm.managerName.trim() || null,
      status: editForm.status,
    })
    cancelEdit()
    successMessage.value = '仓库更新成功。'
    await warehouseList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    updating.value = false
  }
}
</script>

<template>
  <section class="warehouse-list-page">
    <div class="page-toolbar">
      <button v-if="canManage" class="create-button" type="button" @click="openCreateModal">创建仓库</button>
    </div>
    <FilterBar @submit="warehouseList.applyFilters" @reset="warehouseList.resetFilters">
      <label>
        关键字
        <input v-model="warehouseList.filters.keyword" placeholder="仓库编码、名称或负责人" />
      </label>
      <label>
        状态
        <SelectField v-model="warehouseList.filters.status" :options="warehouseStatusOptions" />
      </label>
    </FilterBar>
    <p v-if="successMessage" class="warehouse-create-status" role="status">{{ successMessage }}</p>

    <CreateFormModal
      :open="showCreateModal"
      title="创建仓库"
      :submitting="submitting"
      :error="formError"
      @close="closeCreateModal"
      @submit="handleSubmit"
    >
      <label v-if="showCooperativeSelector">
        合作社
        <select v-model="form.cooperativeId" required>
          <option value="" disabled>请选择合作社</option>
          <option v-for="cooperative in cooperativeState.data" :key="cooperative.id" :value="cooperative.id">
            {{ cooperative.name }}
          </option>
        </select>
      </label>
      <GeneratedCodeField label="编码" format="WH-XXXXXX" />
      <label>
        名称
        <input v-model="form.name" name="name" required minlength="2" maxlength="100" />
      </label>
      <label>
        地址
        <input v-model="form.address" name="address" maxlength="255" />
      </label>
      <label>
        负责人
        <input v-model="form.managerName" name="managerName" maxlength="50" />
      </label>
    </CreateFormModal>

    <form v-if="canManage && editingWarehouseId" class="warehouse-edit-form" @submit.prevent="handleUpdate">
      <h2>编辑仓库</h2>
      <label>
        名称
        <input v-model="editForm.name" name="edit-name" required minlength="2" maxlength="100" />
      </label>
      <label>
        地址
        <input v-model="editForm.address" name="edit-address" maxlength="255" />
      </label>
      <label>
        负责人
        <input v-model="editForm.managerName" name="edit-manager" maxlength="50" />
      </label>
      <label>
        状态
        <select v-model="editForm.status">
          <option value="ACTIVE">启用</option>
          <option value="INACTIVE">停用</option>
        </select>
      </label>
      <button type="submit" :disabled="updating">{{ updating ? '保存中…' : '保存' }}</button>
      <button type="button" :disabled="updating" @click="cancelEdit">取消</button>
    </form>

    <PageState
      :loading="warehouseList.loading"
      :error="warehouseList.error"
      :empty="warehouseList.items.length === 0"
      @retry="warehouseList.loadData"
    >
      <table>
        <caption>仓库列表</caption>
        <thead>
          <tr>
            <th scope="col">编码</th>
            <th scope="col">名称</th>
            <th scope="col">地址</th>
            <th scope="col">负责人</th>
            <th scope="col">状态</th>
            <th v-if="canManage" scope="col">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="warehouse in warehouseList.items" :key="warehouse.id">
            <td>{{ warehouse.code }}</td>
            <td>{{ warehouse.name }}</td>
            <td>{{ warehouse.address || '—' }}</td>
            <td>{{ warehouse.managerName || '—' }}</td>
            <td><StatusBadge :label="warehouse.status === 'ACTIVE' ? '启用' : '停用'" :tone="warehouse.status === 'ACTIVE' ? 'success' : 'neutral'" /></td>
            <td v-if="canManage">
              <button type="button" @click="beginEdit(warehouse)">编辑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </PageState>
    <PaginationBar
      :page="warehouseList.pagination.page"
      :total-pages="warehouseList.pagination.totalPages"
      :total-items="warehouseList.pagination.totalItems"
      :page-size="warehouseList.pagination.pageSize"
      @change="warehouseList.goToPage"
      @page-size-change="warehouseList.setPageSize"
    />
  </section>
</template>

<style scoped>
.warehouse-list-page {
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

.warehouse-list-page > .page-state {
  overflow-x: auto;
}

.warehouse-list-page > .page-state table {
  min-width: 50rem;
}

.warehouse-edit-form {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.warehouse-edit-form h2 {
  grid-column: 1 / -1;
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.warehouse-edit-form > label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.warehouse-edit-form > p {
  grid-column: 1 / -1;
  margin: 0;
  font-size: var(--font-size-sm);
}

.warehouse-edit-form > p[role='alert'] {
  color: var(--color-danger);
}

.warehouse-edit-form > p[role='status'] {
  color: var(--color-success);
}

.warehouse-edit-form > button {
  justify-self: start;
}

@media (max-width: 48rem) {
  .warehouse-edit-form {
    grid-template-columns: 1fr;
    padding: var(--space-4);
  }

  .warehouse-edit-form h2,
  .warehouse-edit-form > p {
    grid-column: auto;
  }

  .warehouse-edit-form > button {
    justify-self: stretch;
  }
}

.warehouse-create-status {
  margin: 0;
  color: var(--color-success);
  font-size: var(--font-size-sm);
}
</style>
