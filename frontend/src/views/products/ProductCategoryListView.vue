<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import {
  createProductCategory,
  listProductCategories,
  updateProductCategory,
} from '@/api/product-categories'
import { useListPage } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const { items, loading, error, loadData } = useListPage(listProductCategories)
const authStore = useAuthStore()
const canManage = computed(() => authStore.hasPermission('product:manage'))
const submitting = ref(false)
const updating = ref(false)
const formError = ref('')
const successMessage = ref('')
const editingCategoryId = ref<string | null>(null)
const form = reactive({
  code: '',
  name: '',
  description: '',
})
const editForm = reactive({
  name: '',
  description: '',
  isActive: true,
})

function resetForm(): void {
  form.code = ''
  form.name = ''
  form.description = ''
}

async function handleSubmit(): Promise<void> {
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    await createProductCategory({
      code: form.code.trim(),
      name: form.name.trim(),
      description: form.description.trim() || null,
    })
    resetForm()
    successMessage.value = '产品分类创建成功。'
    await loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

function beginEdit(category: (typeof items.value)[number]): void {
  editingCategoryId.value = category.id
  editForm.name = category.name
  editForm.description = category.description ?? ''
  editForm.isActive = category.isActive
  formError.value = ''
  successMessage.value = ''
}

function cancelEdit(): void {
  editingCategoryId.value = null
  formError.value = ''
}

async function handleUpdate(): Promise<void> {
  if (!editingCategoryId.value) return
  updating.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    await updateProductCategory(editingCategoryId.value, {
      name: editForm.name.trim(),
      description: editForm.description.trim() || null,
      isActive: editForm.isActive,
    })
    cancelEdit()
    successMessage.value = '产品分类更新成功。'
    await loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    updating.value = false
  }
}
</script>

<template>
  <section class="product-category-list-page">
    <PageHeader eyebrow="基础资料" title="产品分类" description="查看当前合作社的产品分类。" />
    <PageContext />
    <form v-if="canManage" class="product-category-create-form" @submit.prevent="handleSubmit">
      <h2>新增产品分类</h2>
      <label>
        编码
        <input v-model="form.code" name="code" required maxlength="32" />
      </label>
      <label>
        名称
        <input v-model="form.name" name="name" required maxlength="80" />
      </label>
      <label>
        描述
        <textarea v-model="form.description" name="description" maxlength="255" />
      </label>
      <button type="submit" :disabled="submitting">{{ submitting ? '提交中…' : '创建' }}</button>
      <p v-if="formError" role="alert">{{ formError }}</p>
      <p v-if="successMessage" role="status">{{ successMessage }}</p>
    </form>
    <form v-if="canManage && editingCategoryId" class="product-category-edit-form" @submit.prevent="handleUpdate">
      <h2>编辑产品分类</h2>
      <label>
        名称
        <input v-model="editForm.name" name="edit-name" required maxlength="80" />
      </label>
      <label>
        描述
        <textarea v-model="editForm.description" name="edit-description" maxlength="255" />
      </label>
      <label>
        <input v-model="editForm.isActive" type="checkbox" name="edit-is-active" />
        启用
      </label>
      <button type="submit" :disabled="updating">{{ updating ? '保存中…' : '保存' }}</button>
      <button type="button" :disabled="updating" @click="cancelEdit">取消</button>
    </form>
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <table>
        <caption>产品分类列表</caption>
        <thead>
          <tr>
            <th scope="col">编码</th>
            <th scope="col">名称</th>
            <th scope="col">描述</th>
            <th scope="col">状态</th>
            <th v-if="canManage" scope="col">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="category in items" :key="category.id">
            <td>{{ category.code }}</td>
            <td>{{ category.name }}</td>
            <td>{{ category.description || '—' }}</td>
            <td><StatusBadge :label="category.isActive ? '启用' : '停用'" :tone="category.isActive ? 'success' : 'neutral'" /></td>
            <td v-if="canManage">
              <button type="button" @click="beginEdit(category)">编辑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </PageState>
  </section>
</template>
