<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import PageState from '@/components/common/PageState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import {
  createProduct,
  listProducts,
  updateProduct,
  type ProductCreatePayload,
  type ProductUpdatePayload,
} from '@/api/products'
import { listProductCategories } from '@/api/product-categories'
import { usePageData, usePaginatedList } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import type { ProductUnit } from '@/types/resources'
import { getApiErrorMessage } from '@/utils/api-error'

const productList = usePaginatedList(listProducts)
const categoryState = usePageData(
  () => listProductCategories({ isActive: true, pageSize: 100 }),
  [],
)
const authStore = useAuthStore()
const canManage = computed(() => authStore.hasPermission('product:manage'))
const submitting = ref(false)
const updating = ref(false)
const formError = ref('')
const successMessage = ref('')
const editingProductId = ref<string | null>(null)
const units: Array<{ value: ProductUnit; label: string }> = [
  { value: 'KG', label: '千克' },
  { value: 'TON', label: '吨' },
  { value: 'BOX', label: '箱' },
  { value: 'PIECE', label: '件' },
]
const form = reactive<ProductCreatePayload>({
  categoryId: '',
  code: '',
  name: '',
  unit: 'KG',
  shelfLifeDays: 1,
  safetyStock: 0,
})
const editForm = reactive<ProductUpdatePayload>({
  name: '',
  unit: 'KG',
  shelfLifeDays: 1,
  safetyStock: 0,
  isActive: true,
})

function categoryName(categoryId: string): string {
  return categoryState.data.find((category) => category.id === categoryId)?.name ?? '—'
}

function resetForm(): void {
  form.categoryId = ''
  form.code = ''
  form.name = ''
  form.unit = 'KG'
  form.shelfLifeDays = 1
  form.safetyStock = 0
}

async function handleSubmit(): Promise<void> {
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    await createProduct({
      categoryId: form.categoryId,
      code: form.code.trim() || undefined,
      name: form.name.trim(),
      unit: form.unit,
      shelfLifeDays: form.shelfLifeDays,
      safetyStock: form.safetyStock,
    })
    resetForm()
    successMessage.value = '产品创建成功。'
    await productList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

function beginEdit(product: (typeof productList.items)[number]): void {
  editingProductId.value = product.id
  editForm.name = product.name
  editForm.unit = product.unit
  editForm.shelfLifeDays = product.shelfLifeDays
  editForm.safetyStock = product.safetyStock
  editForm.isActive = product.isActive
  formError.value = ''
  successMessage.value = ''
}

function cancelEdit(): void {
  editingProductId.value = null
  formError.value = ''
}

async function handleUpdate(): Promise<void> {
  if (!editingProductId.value) return
  updating.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    await updateProduct(editingProductId.value, {
      name: editForm.name.trim(),
      unit: editForm.unit,
      shelfLifeDays: editForm.shelfLifeDays,
      safetyStock: editForm.safetyStock,
      isActive: editForm.isActive,
    })
    cancelEdit()
    successMessage.value = '产品更新成功。'
    await productList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    updating.value = false
  }
}
</script>

<template>
  <section class="product-list-page">
    <PageHeader eyebrow="基础资料" title="产品管理" description="维护合作社产品和库存基础信息。" />
    <PageContext />
    <form v-if="canManage" class="product-create-form" @submit.prevent="handleSubmit">
      <h2>新增产品</h2>
      <label>
        产品分类
        <div class="field-with-action">
          <select v-model="form.categoryId" name="categoryId" required>
            <option value="" disabled>请选择产品分类</option>
            <option v-for="category in categoryState.data" :key="category.id" :value="category.id">
              {{ category.name }}
            </option>
          </select>
          <RouterLink class="inline-link" :to="{ name: 'product-categories' }">
            管理分类
          </RouterLink>
        </div>
        <span v-if="!categoryState.loading && !categoryState.error && categoryState.data.length === 0" class="field-help" role="status">
          暂无启用分类，请先到产品分类中新增分类。
        </span>
      </label>
      <label>
        编码
        <input
          v-model="form.code"
          name="code"
          maxlength="32"
          placeholder="不填则自动生成，如 VEGETABLE-A1B2C3"
        />
        <span class="field-help">如已有内部编码，可手动填写；留空由系统自动生成，创建后不可修改。</span>
      </label>
      <label>
        名称
        <input v-model="form.name" name="name" required maxlength="100" />
      </label>
      <label>
        计量单位
        <select v-model="form.unit" name="unit" required>
          <option v-for="unit in units" :key="unit.value" :value="unit.value">{{ unit.label }}</option>
        </select>
      </label>
      <label>
        保质期（天）
        <input v-model.number="form.shelfLifeDays" type="number" name="shelfLifeDays" min="1" required />
      </label>
      <label>
        安全库存
        <input v-model.number="form.safetyStock" type="number" name="safetyStock" min="0" step="0.001" required />
      </label>
      <button type="submit" :disabled="submitting || categoryState.loading">
        {{ submitting ? '提交中…' : '创建' }}
      </button>
      <p v-if="formError" role="alert">{{ formError }}</p>
      <p v-if="categoryState.error" role="alert">{{ categoryState.error }}</p>
      <p v-if="successMessage" role="status">{{ successMessage }}</p>
    </form>
    <form v-if="canManage && editingProductId" class="product-edit-form" @submit.prevent="handleUpdate">
      <h2>编辑产品</h2>
      <label>
        名称
        <input v-model="editForm.name" name="edit-name" required maxlength="100" />
      </label>
      <label>
        计量单位
        <select v-model="editForm.unit" name="edit-unit" required>
          <option v-for="unit in units" :key="unit.value" :value="unit.value">{{ unit.label }}</option>
        </select>
      </label>
      <label>
        保质期（天）
        <input v-model.number="editForm.shelfLifeDays" type="number" name="edit-shelf-life" min="1" required />
      </label>
      <label>
        安全库存
        <input v-model.number="editForm.safetyStock" type="number" name="edit-safety-stock" min="0" step="0.001" required />
      </label>
      <label>
        <input v-model="editForm.isActive" type="checkbox" name="edit-is-active" />
        启用
      </label>
      <button type="submit" :disabled="updating">{{ updating ? '保存中…' : '保存' }}</button>
      <button type="button" :disabled="updating" @click="cancelEdit">取消</button>
    </form>
    <PageState
      :loading="productList.loading"
      :error="productList.error"
      :empty="productList.items.length === 0"
      @retry="productList.loadData"
    >
      <table>
        <caption>产品列表</caption>
        <thead>
          <tr>
            <th scope="col">编码</th>
            <th scope="col">名称</th>
            <th scope="col">分类</th>
            <th scope="col">单位</th>
            <th scope="col">保质期（天）</th>
            <th scope="col">安全库存</th>
            <th scope="col">状态</th>
            <th v-if="canManage" scope="col">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in productList.items" :key="product.id">
            <td>{{ product.code }}</td>
            <td>{{ product.name }}</td>
            <td>{{ categoryName(product.categoryId) }}</td>
            <td>{{ product.unit }}</td>
            <td>{{ product.shelfLifeDays }}</td>
            <td>{{ product.safetyStock }}</td>
            <td><StatusBadge :label="product.isActive ? '启用' : '停用'" :tone="product.isActive ? 'success' : 'neutral'" /></td>
            <td v-if="canManage">
              <button type="button" @click="beginEdit(product)">编辑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </PageState>
    <PaginationBar
      :page="productList.pagination.page"
      :total-pages="productList.pagination.totalPages"
      :total-items="productList.pagination.totalItems"
      :page-size="productList.pagination.pageSize"
      :page-size-options="[10]"
      @change="productList.goToPage"
      @page-size-change="productList.setPageSize"
    />
  </section>
</template>

<style scoped>
.product-list-page {
  display: grid;
  gap: var(--space-5);
}

.product-list-page > .page-state {
  overflow-x: auto;
}

.product-list-page > .page-state table {
  min-width: 62rem;
}

.product-create-form,
.product-edit-form {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.product-create-form h2,
.product-edit-form h2 {
  grid-column: 1 / -1;
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.product-create-form > label,
.product-edit-form > label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.field-with-action {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.field-with-action select {
  min-width: 0;
  flex: 1;
}

.inline-link {
  flex: 0 0 auto;
  white-space: nowrap;
  color: var(--color-accent);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.field-help {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 400;
  line-height: 1.5;
}

.product-create-form > p,
.product-edit-form > p {
  grid-column: 1 / -1;
  margin: 0;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

.product-create-form > p[role='status'],
.product-edit-form > p[role='status'] {
  color: var(--color-success);
}

.product-create-form > button,
.product-edit-form > button {
  justify-self: start;
}

@media (max-width: 48rem) {
  .product-create-form,
  .product-edit-form {
    grid-template-columns: 1fr;
    padding: var(--space-4);
  }

  .product-create-form h2,
  .product-edit-form h2,
  .product-create-form > p,
  .product-edit-form > p {
    grid-column: auto;
  }

  .product-create-form > button,
  .product-edit-form > button {
    justify-self: stretch;
  }

  .field-with-action {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
