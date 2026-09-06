<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { listCooperatives } from '@/api/cooperatives'
import {
  createWarehouse,
  listWarehouses,
  updateWarehouse,
} from '@/api/warehouses'
import type { WarehouseStatus } from '@/api/warehouses'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useListPage, usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const { items, loading, error, loadData } = useListPage(listWarehouses)
const authStore = useAuthStore()
const canManage = computed(() => authStore.hasPermission('warehouse:manage'))
const showCooperativeSelector = computed(() => authStore.role === 'SYSTEM_ADMIN')
const cooperativeState = usePageData(
  () => (showCooperativeSelector.value ? listCooperatives() : Promise.resolve([])),
  [],
)
const submitting = ref(false)
const updating = ref(false)
const formError = ref('')
const successMessage = ref('')
const editingWarehouseId = ref<string | null>(null)
const form = reactive({
  cooperativeId: '',
  code: '',
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
  form.code = ''
  form.name = ''
  form.address = ''
  form.managerName = ''
}

async function handleSubmit(): Promise<void> {
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    await createWarehouse({
      cooperativeId: form.cooperativeId || null,
      code: form.code.trim(),
      name: form.name.trim(),
      address: form.address.trim() || null,
      managerName: form.managerName.trim() || null,
    })
    resetForm()
    successMessage.value = '仓库创建成功。'
    await loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

function beginEdit(warehouse: (typeof items.value)[number]): void {
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
    await loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    updating.value = false
  }
}
</script>

<template>
  <section class="warehouse-list-page">
    <PageHeader eyebrow="组织管理" title="仓库管理" description="维护仓库基础信息和启停状态。" />
    <PageContext />
    <form v-if="canManage" class="warehouse-create-form" @submit.prevent="handleSubmit">
      <h2>新增仓库</h2>
      <label v-if="showCooperativeSelector">
        合作社
        <select v-model="form.cooperativeId" required>
          <option value="" disabled>请选择合作社</option>
          <option v-for="cooperative in cooperativeState.data" :key="cooperative.id" :value="cooperative.id">
            {{ cooperative.name }}
          </option>
        </select>
      </label>
      <label>
        编码
        <input v-model="form.code" name="code" required minlength="2" maxlength="32" />
      </label>
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
      <button type="submit" :disabled="submitting">{{ submitting ? '提交中…' : '创建' }}</button>
      <p v-if="formError" role="alert">{{ formError }}</p>
      <p v-if="successMessage" role="status">{{ successMessage }}</p>
    </form>

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

    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
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
          <tr v-for="warehouse in items" :key="warehouse.id">
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
  </section>
</template>

<style scoped>
.warehouse-list-page {
  display: grid;
  gap: var(--space-5);
}

.warehouse-list-page > .page-state {
  overflow-x: auto;
}

.warehouse-list-page > .page-state table {
  min-width: 50rem;
}

.warehouse-create-form,
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

.warehouse-create-form h2,
.warehouse-edit-form h2 {
  grid-column: 1 / -1;
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.warehouse-create-form > label,
.warehouse-edit-form > label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.warehouse-create-form > p,
.warehouse-edit-form > p {
  grid-column: 1 / -1;
  margin: 0;
  font-size: var(--font-size-sm);
}

.warehouse-create-form > p[role='alert'],
.warehouse-edit-form > p[role='alert'] {
  color: var(--color-danger);
}

.warehouse-create-form > p[role='status'],
.warehouse-edit-form > p[role='status'] {
  color: var(--color-success);
}

.warehouse-create-form > button,
.warehouse-edit-form > button {
  justify-self: start;
}

@media (max-width: 48rem) {
  .warehouse-create-form,
  .warehouse-edit-form {
    grid-template-columns: 1fr;
    padding: var(--space-4);
  }

  .warehouse-create-form h2,
  .warehouse-edit-form h2,
  .warehouse-create-form > p,
  .warehouse-edit-form > p {
    grid-column: auto;
  }

  .warehouse-create-form > button,
  .warehouse-edit-form > button {
    justify-self: stretch;
  }
}
</style>
