<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import FilterBar from '@/components/common/FilterBar.vue'
import {
  createCooperative,
  listCooperativesPage,
  updateCooperative,
} from '@/api/cooperatives'
import type { CooperativeListParams, CooperativeStatus } from '@/api/cooperatives'
import CreateFormModal from '@/components/common/CreateFormModal.vue'
import GeneratedCodeField from '@/components/common/GeneratedCodeField.vue'
import PageState from '@/components/common/PageState.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import SelectField, { type SelectFieldOption } from '@/components/common/SelectField.vue'
import { useFilteredPaginatedList } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

type CooperativeFilterState = Pick<CooperativeListParams, 'keyword' | 'status'> & {
  keyword: string
  status: CooperativeStatus | ''
}

const cooperativeList = useFilteredPaginatedList(
  (params) => listCooperativesPage({
    ...params,
    keyword: params.keyword || undefined,
    status: params.status || undefined,
  }),
  { keyword: '', status: '' } satisfies CooperativeFilterState,
)
const cooperativeStatusOptions: SelectFieldOption[] = [
  { value: '', label: '全部状态' },
  { value: 'ACTIVE', label: '启用' },
  { value: 'INACTIVE', label: '停用' },
]
const authStore = useAuthStore()
const canManage = computed(() => authStore.hasPermission('cooperative:manage'))
const showCreateModal = ref(false)
const submitting = ref(false)
const updating = ref(false)
const formError = ref('')
const successMessage = ref('')
const editingCooperativeId = ref<string | null>(null)
const form = reactive({
  name: '',
  address: '',
  contactName: '',
  contactPhone: '',
})
const editForm = reactive<{
  name: string
  address: string
  contactName: string
  contactPhone: string
  status: CooperativeStatus
}>({
  name: '',
  address: '',
  contactName: '',
  contactPhone: '',
  status: 'ACTIVE',
})

function resetForm(): void {
  form.name = ''
  form.address = ''
  form.contactName = ''
  form.contactPhone = ''
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
    await createCooperative({
      name: form.name.trim(),
      address: form.address.trim() || null,
      contactName: form.contactName.trim() || null,
      contactPhone: form.contactPhone.trim() || null,
    })
    resetForm()
    showCreateModal.value = false
    successMessage.value = '合作社创建成功。'
    await cooperativeList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

function beginEdit(cooperative: (typeof cooperativeList.items)[number]): void {
  editingCooperativeId.value = cooperative.id
  editForm.name = cooperative.name
  editForm.address = cooperative.address ?? ''
  editForm.contactName = cooperative.contactName ?? ''
  editForm.contactPhone = cooperative.contactPhone ?? ''
  editForm.status = cooperative.status === 'INACTIVE' ? 'INACTIVE' : 'ACTIVE'
  formError.value = ''
  successMessage.value = ''
}

function cancelEdit(): void {
  editingCooperativeId.value = null
  formError.value = ''
}

async function handleUpdate(): Promise<void> {
  if (!editingCooperativeId.value) return
  updating.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    await updateCooperative(editingCooperativeId.value, {
      name: editForm.name.trim(),
      address: editForm.address.trim() || null,
      contactName: editForm.contactName.trim() || null,
      contactPhone: editForm.contactPhone.trim() || null,
      status: editForm.status,
    })
    cancelEdit()
    successMessage.value = '合作社更新成功。'
    await cooperativeList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    updating.value = false
  }
}
</script>

<template>
  <section class="cooperative-list-page">
    <div class="page-toolbar">
      <button v-if="canManage" class="create-button" type="button" @click="openCreateModal">创建合作社</button>
    </div>
    <FilterBar @submit="cooperativeList.applyFilters" @reset="cooperativeList.resetFilters">
      <label>
        关键字
        <input v-model="cooperativeList.filters.keyword" placeholder="合作社编码或名称" />
      </label>
      <label>
        状态
        <SelectField v-model="cooperativeList.filters.status" :options="cooperativeStatusOptions" />
      </label>
    </FilterBar>
    <p v-if="successMessage" class="create-status" role="status">{{ successMessage }}</p>

    <CreateFormModal
      :open="showCreateModal"
      title="创建合作社"
      :submitting="submitting"
      :error="formError"
      @close="closeCreateModal"
      @submit="handleSubmit"
    >
      <GeneratedCodeField label="编码" format="COOP-XXXXXX" />
      <label>
        名称
        <input v-model="form.name" name="name" required minlength="2" maxlength="100" />
      </label>
      <label>
        地址
        <input v-model="form.address" name="address" maxlength="255" />
      </label>
      <label>
        联系人
        <input v-model="form.contactName" name="contactName" maxlength="50" />
      </label>
      <label>
        联系电话
        <input
          v-model="form.contactPhone"
          name="contactPhone"
          inputmode="numeric"
          pattern="1[3-9][0-9]{9}"
          maxlength="11"
        />
      </label>
    </CreateFormModal>

    <form v-if="canManage && editingCooperativeId" class="cooperative-edit-form" @submit.prevent="handleUpdate">
      <h2>编辑合作社</h2>
      <label>
        名称
        <input v-model="editForm.name" name="edit-name" required minlength="2" maxlength="100" />
      </label>
      <label>
        地址
        <input v-model="editForm.address" name="edit-address" maxlength="255" />
      </label>
      <label>
        联系人
        <input v-model="editForm.contactName" name="edit-contact-name" maxlength="50" />
      </label>
      <label>
        联系电话
        <input
          v-model="editForm.contactPhone"
          name="edit-contact-phone"
          inputmode="numeric"
          pattern="1[3-9][0-9]{9}"
          maxlength="11"
        />
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
      :loading="cooperativeList.loading"
      :error="cooperativeList.error"
      :empty="cooperativeList.items.length === 0"
      @retry="cooperativeList.loadData"
    >
      <table>
        <caption>合作社列表</caption>
        <thead>
          <tr>
            <th scope="col">编码</th>
            <th scope="col">名称</th>
            <th scope="col">联系人</th>
            <th scope="col">联系电话</th>
            <th scope="col">地址</th>
            <th scope="col">状态</th>
            <th v-if="canManage" scope="col">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cooperative in cooperativeList.items" :key="cooperative.id">
            <td>{{ cooperative.code }}</td>
            <td>{{ cooperative.name }}</td>
            <td>{{ cooperative.contactName || '—' }}</td>
            <td>{{ cooperative.contactPhone || '—' }}</td>
            <td>{{ cooperative.address || '—' }}</td>
            <td><StatusBadge :label="cooperative.status === 'ACTIVE' ? '启用' : '停用'" :tone="cooperative.status === 'ACTIVE' ? 'success' : 'neutral'" /></td>
            <td v-if="canManage">
              <button type="button" @click="beginEdit(cooperative)">编辑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </PageState>
    <PaginationBar
      :page="cooperativeList.pagination.page"
      :total-pages="cooperativeList.pagination.totalPages"
      :total-items="cooperativeList.pagination.totalItems"
      :page-size="cooperativeList.pagination.pageSize"
      @change="cooperativeList.goToPage"
      @page-size-change="cooperativeList.setPageSize"
    />
  </section>
</template>

<style scoped>
.cooperative-list-page {
  display: grid;
  gap: var(--space-5);
}

.cooperative-list-page > .page-state {
  overflow-x: auto;
}

.cooperative-list-page > .page-state table {
  min-width: 48rem;
}

.cooperative-edit-form {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.cooperative-edit-form h2 {
  grid-column: 1 / -1;
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.cooperative-edit-form > label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.cooperative-edit-form > p {
  grid-column: 1 / -1;
  margin: 0;
  font-size: var(--font-size-sm);
}

.cooperative-edit-form > p[role='alert'] {
  color: var(--color-danger);
}

.cooperative-edit-form > p[role='status'] {
  color: var(--color-success);
}

.cooperative-edit-form > button {
  justify-self: start;
}

@media (max-width: 48rem) {
  .cooperative-edit-form {
    grid-template-columns: 1fr;
    padding: var(--space-4);
  }

  .cooperative-edit-form h2,
  .cooperative-edit-form > p {
    grid-column: auto;
  }

  .cooperative-edit-form > button {
    justify-self: stretch;
  }
}

.page-toolbar {
  display: flex;
  justify-content: flex-end;
}

.create-button {
  min-height: 2.5rem;
  padding: var(--space-2) var(--space-4);
}

.create-status {
  margin: 0;
  color: var(--color-success);
  font-size: var(--font-size-sm);
}
</style>
