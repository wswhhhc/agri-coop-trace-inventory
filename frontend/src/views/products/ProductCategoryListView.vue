<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import PageState from '@/components/common/PageState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import GeneratedCodeField from '@/components/common/GeneratedCodeField.vue'
import {
  createProductCategory,
  listProductCategoriesPage,
  updateProductCategory,
} from '@/api/product-categories'
import PaginationBar from '@/components/common/PaginationBar.vue'
import { usePaginatedList } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const categoryList = usePaginatedList(listProductCategoriesPage)
const authStore = useAuthStore()
const canManage = computed(() => authStore.hasPermission('product:manage'))
const submitting = ref(false)
const updating = ref(false)
const formError = ref('')
const successMessage = ref('')
const editingCategoryId = ref<string | null>(null)
const form = reactive({
  name: '',
  description: '',
})
const editForm = reactive({
  name: '',
  description: '',
  isActive: true,
})

function resetForm(): void {
  form.name = ''
  form.description = ''
}

async function handleSubmit(): Promise<void> {
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    await createProductCategory({
      name: form.name.trim(),
      description: form.description.trim() || null,
    })
    resetForm()
    successMessage.value = '产品分类创建成功。'
    await categoryList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

function beginEdit(category: (typeof categoryList.items)[number]): void {
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
    await categoryList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    updating.value = false
  }
}
</script>

<template>
  <section class="product-category-list-page">
    <form v-if="canManage" class="product-category-create-form" @submit.prevent="handleSubmit">
      <h2>新增产品分类</h2>
      <GeneratedCodeField label="编码" format="CAT-XXXXXX" />
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
    <PageState
      :loading="categoryList.loading"
      :error="categoryList.error"
      :empty="categoryList.items.length === 0"
      @retry="categoryList.loadData"
    >
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
          <tr v-for="category in categoryList.items" :key="category.id">
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
    <PaginationBar
      :page="categoryList.pagination.page"
      :total-pages="categoryList.pagination.totalPages"
      :total-items="categoryList.pagination.totalItems"
      :page-size="categoryList.pagination.pageSize"
      @change="categoryList.goToPage"
      @page-size-change="categoryList.setPageSize"
    />
  </section>
</template>

<style scoped>
.product-category-list-page {
  display: grid;
  gap: var(--space-5);
}

.product-category-list-page > .page-state {
  overflow-x: auto;
}

.product-category-list-page > .page-state table {
  min-width: 46rem;
}

.product-category-create-form,
.product-category-edit-form {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.product-category-create-form h2,
.product-category-edit-form h2 {
  grid-column: 1 / -1;
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.product-category-create-form > label,
.product-category-edit-form > label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.product-category-create-form > label:nth-of-type(2),
.product-category-edit-form > label:nth-of-type(2),
.product-category-create-form > p,
.product-category-edit-form > p {
  grid-column: 1 / -1;
}

.product-category-create-form > button,
.product-category-edit-form > button {
  justify-self: start;
}

.product-category-create-form > p,
.product-category-edit-form > p {
  margin: 0;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

.product-category-create-form > p[role='status'],
.product-category-edit-form > p[role='status'] {
  color: var(--color-success);
}

@media (max-width: 48rem) {
  .product-category-create-form,
  .product-category-edit-form {
    grid-template-columns: 1fr;
    padding: var(--space-4);
  }

  .product-category-create-form h2,
  .product-category-edit-form h2,
  .product-category-create-form > label:nth-of-type(2),
  .product-category-edit-form > label:nth-of-type(2),
  .product-category-create-form > p,
  .product-category-edit-form > p {
    grid-column: auto;
  }

  .product-category-create-form > button,
  .product-category-edit-form > button {
    justify-self: stretch;
  }
}
</style>
