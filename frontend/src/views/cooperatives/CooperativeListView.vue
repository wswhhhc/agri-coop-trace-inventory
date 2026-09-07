<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import {
  createCooperative,
  listCooperatives,
  updateCooperative,
} from '@/api/cooperatives'
import type { CooperativeStatus } from '@/api/cooperatives'
import GeneratedCodeField from '@/components/common/GeneratedCodeField.vue'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useListPage } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const { items, loading, error, loadData } = useListPage(listCooperatives)
const authStore = useAuthStore()
const canManage = computed(() => authStore.hasPermission('cooperative:manage'))
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
    successMessage.value = '合作社创建成功。'
    await loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

function beginEdit(cooperative: (typeof items.value)[number]): void {
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
    await loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    updating.value = false
  }
}
</script>

<template>
  <section class="cooperative-list-page">
    <PageHeader eyebrow="组织管理" title="合作社管理" description="维护平台合作社信息和启停状态。" />
    <PageContext />
    <form v-if="canManage" class="cooperative-create-form" @submit.prevent="handleSubmit">
      <h2>新增合作社</h2>
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
      <button type="submit" :disabled="submitting">{{ submitting ? '提交中…' : '创建' }}</button>
      <p v-if="formError" role="alert">{{ formError }}</p>
      <p v-if="successMessage" role="status">{{ successMessage }}</p>
    </form>

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

    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
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
          <tr v-for="cooperative in items" :key="cooperative.id">
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

.cooperative-create-form,
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

.cooperative-create-form h2,
.cooperative-edit-form h2 {
  grid-column: 1 / -1;
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.cooperative-create-form > label,
.cooperative-edit-form > label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.cooperative-create-form > p,
.cooperative-edit-form > p {
  grid-column: 1 / -1;
  margin: 0;
  font-size: var(--font-size-sm);
}

.cooperative-create-form > p[role='alert'],
.cooperative-edit-form > p[role='alert'] {
  color: var(--color-danger);
}

.cooperative-create-form > p[role='status'],
.cooperative-edit-form > p[role='status'] {
  color: var(--color-success);
}

.cooperative-create-form > button,
.cooperative-edit-form > button {
  justify-self: start;
}

@media (max-width: 48rem) {
  .cooperative-create-form,
  .cooperative-edit-form {
    grid-template-columns: 1fr;
    padding: var(--space-4);
  }

  .cooperative-create-form h2,
  .cooperative-edit-form h2,
  .cooperative-create-form > p,
  .cooperative-edit-form > p {
    grid-column: auto;
  }

  .cooperative-create-form > button,
  .cooperative-edit-form > button {
    justify-self: stretch;
  }
}
</style>
