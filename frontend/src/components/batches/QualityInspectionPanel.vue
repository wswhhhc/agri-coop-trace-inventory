<script setup lang="ts">
import { reactive, ref } from 'vue'

import {
  createQualityInspection,
  listQualityInspectionsPage,
  type InspectionConclusion,
  type QualityInspectionListParams,
  type QualityInspectionItemCreatePayload,
} from '@/api/quality-inspections'
import { uploadFile } from '@/api/files'
import FilterBar from '@/components/common/FilterBar.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import SelectField, { type SelectFieldOption } from '@/components/common/SelectField.vue'
import { useFilteredPaginatedList } from '@/composables/usePageData'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { getApiErrorMessage } from '@/utils/api-error'
import { formatInspectionConclusion } from '@/utils/traceability-format'

const props = defineProps<{
  batchId: string
  canManage: boolean
}>()

type QualityInspectionFilterState = Pick<QualityInspectionListParams, 'conclusion'> & {
  conclusion: InspectionConclusion | ''
}
const inspectionList = useFilteredPaginatedList(
  (params) => listQualityInspectionsPage(props.batchId, {
    ...params,
    conclusion: params.conclusion || undefined,
  }),
  { conclusion: '' } satisfies QualityInspectionFilterState,
)
const conclusionOptions: SelectFieldOption[] = [
  { value: '', label: '全部结论' },
  { value: 'PENDING', label: '待定' },
  { value: 'PASSED', label: '合格' },
  { value: 'FAILED', label: '不合格' },
]
const submitting = ref(false)
const formError = ref('')
const successMessage = ref('')
const form = reactive({
  inspectionDate: '',
  conclusion: 'PENDING' as InspectionConclusion,
  remarks: '',
})
const inspectionItems = ref<QualityInspectionItemCreatePayload[]>([createItem()])
const attachments = ref<File[]>([])

function conclusionTone(value: string): 'success' | 'warning' | 'danger' {
  if (value === 'PASSED') return 'success'
  if (value === 'FAILED') return 'danger'
  return 'warning'
}

function createItem(): QualityInspectionItemCreatePayload {
  return { name: '', value: '', unit: null, standard: '', isQualified: true }
}

function addItem(): void {
  inspectionItems.value.push(createItem())
}

function removeItem(index: number): void {
  if (inspectionItems.value.length > 1) inspectionItems.value.splice(index, 1)
}

function resetForm(): void {
  form.inspectionDate = ''
  form.conclusion = 'PENDING'
  form.remarks = ''
  inspectionItems.value = [createItem()]
  attachments.value = []
}

function handleFileChange(event: Event): void {
  const input = event.target as HTMLInputElement
  attachments.value = Array.from(input.files ?? [])
}

async function handleSubmit(): Promise<void> {
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    const uploadedFiles = await Promise.all(attachments.value.map((file) => uploadFile(file)))
    await createQualityInspection(props.batchId, {
      inspectionDate: form.inspectionDate,
      conclusion: form.conclusion,
      items: inspectionItems.value.map((item) => ({
        ...item,
        name: item.name.trim(),
        value: item.value.trim(),
        standard: item.standard.trim(),
        unit: item.unit?.trim() || null,
      })),
      remarks: form.remarks.trim() || null,
      attachmentFileIds: uploadedFiles.map((file) => file.id),
    })
    resetForm()
    successMessage.value = '质检记录创建成功。'
    await loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="quality-inspection-panel" aria-labelledby="quality-inspection-title">
    <header class="module-header">
      <div>
        <p class="module-kicker">质量把关</p>
        <h2 id="quality-inspection-title">质检记录</h2>
        <p class="module-description">查看每次检测结论与指标明细，确保批次质量可核验。</p>
      </div>
      <span class="module-count">共 {{ inspectionList.pagination.totalItems }} 条</span>
    </header>
    <FilterBar class="inspection-filter" @submit="inspectionList.applyFilters" @reset="inspectionList.resetFilters">
      <label>
        质检结论
        <SelectField v-model="inspectionList.filters.conclusion" :options="conclusionOptions" />
      </label>
    </FilterBar>
    <section v-if="inspectionList.loading && inspectionList.items.length === 0" class="module-state" role="status"><p>质检记录加载中…</p></section>
    <section v-else-if="inspectionList.error && inspectionList.items.length === 0" class="module-state module-state--error" role="alert">
      <p>{{ inspectionList.error }}</p>
      <button type="button" @click="inspectionList.loadData">重试</button>
    </section>
    <p v-else-if="inspectionList.items.length === 0" class="module-state">暂无质检记录。</p>
    <div v-else class="inspection-list" :aria-busy="inspectionList.loading">
      <article v-for="inspection in inspectionList.items" :key="inspection.id" class="inspection-record">
      <h3>
        <span>{{ inspection.inspectionNo }}</span>
        <StatusBadge :label="formatInspectionConclusion(inspection.conclusion)" :tone="conclusionTone(inspection.conclusion)" />
      </h3>
      <dl class="inspection-meta">
        <div><dt>检测日期</dt><dd>{{ inspection.inspectionDate }}</dd></div>
        <div><dt>检验人</dt><dd>{{ inspection.inspectorName }}</dd></div>
      </dl>
      <p v-if="inspection.remarks" class="inspection-remark"><span>备注</span>{{ inspection.remarks }}</p>
      <table>
        <caption>质检项目</caption>
        <thead>
          <tr><th scope="col">项目</th><th scope="col">结果</th><th scope="col">标准</th><th scope="col">结论</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in inspection.items" :key="item.id">
            <td>{{ item.name }}</td>
            <td>{{ item.value }}{{ item.unit ? ` ${item.unit}` : '' }}</td>
            <td>{{ item.standard }}</td>
            <td><StatusBadge :label="item.isQualified ? '合格' : '不合格'" :tone="item.isQualified ? 'success' : 'danger'" /></td>
          </tr>
        </tbody>
      </table>
      </article>
    </div>
    <PaginationBar
      :page="inspectionList.pagination.page"
      :total-pages="inspectionList.pagination.totalPages"
      :total-items="inspectionList.pagination.totalItems"
      :page-size="inspectionList.pagination.pageSize"
      @change="inspectionList.goToPage"
      @page-size-change="inspectionList.setPageSize"
    />

    <form v-if="canManage" class="quality-inspection-create-form" @submit.prevent="handleSubmit">
      <h3>新增质检记录</h3>
      <label>
        质检日期
        <input v-model="form.inspectionDate" type="date" name="inspectionDate" required />
      </label>
      <label>
        结论
        <select v-model="form.conclusion" name="conclusion">
          <option value="PENDING">待定</option>
          <option value="PASSED">合格</option>
          <option value="FAILED">不合格</option>
        </select>
      </label>
      <label>
        备注
        <textarea v-model="form.remarks" name="remarks" maxlength="500" />
      </label>
      <label>
        质检附件
        <input type="file" multiple @change="handleFileChange" />
      </label>
      <ul v-if="attachments.length > 0">
        <li v-for="file in attachments" :key="file.name">{{ file.name }}</li>
      </ul>
      <fieldset v-for="(item, index) in inspectionItems" :key="index">
        <legend>检验项目 {{ index + 1 }}</legend>
        <label>项目名称 <input v-model="item.name" required maxlength="100" /></label>
        <label>结果 <input v-model="item.value" required maxlength="100" /></label>
        <label>单位 <input v-model="item.unit" maxlength="20" /></label>
        <label>标准 <input v-model="item.standard" required maxlength="100" /></label>
        <label><input v-model="item.isQualified" type="checkbox" /> 合格</label>
        <button type="button" :disabled="inspectionItems.length === 1" @click="removeItem(index)">删除项目</button>
      </fieldset>
      <button type="button" @click="addItem">增加项目</button>
      <button type="submit" :disabled="submitting">{{ submitting ? '提交中…' : '提交质检' }}</button>
      <p v-if="formError" role="alert">{{ formError }}</p>
      <p v-if="successMessage" role="status">{{ successMessage }}</p>
    </form>
  </section>
</template>

<style scoped>
.quality-inspection-panel {
  display: grid;
  align-content: start;
  gap: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.module-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.module-kicker {
  margin-bottom: var(--space-1);
  color: var(--color-accent);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.08em;
}

.module-header h2 {
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.module-description {
  max-width: 42rem;
  margin: var(--space-2) 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.module-count {
  flex: 0 0 auto;
  border-radius: var(--radius-pill);
  padding: var(--space-1) var(--space-3);
  background: var(--color-brand-soft);
  color: var(--color-brand);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.inspection-filter {
  grid-template-columns: minmax(15rem, 22rem) auto;
  justify-content: start;
  margin: 0;
  padding: var(--space-3);
  border-color: var(--color-brand-soft);
  background: var(--color-surface-muted);
}

.inspection-list {
  display: grid;
  gap: var(--space-3);
}

.inspection-record {
  display: grid;
  gap: var(--space-3);
  min-width: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  background: var(--color-surface-muted);
}

.inspection-record h3 {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: 0;
  font-size: var(--font-size-md);
}

.inspection-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-5);
  margin: 0;
}

.inspection-meta div {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
}

.inspection-meta dt,
.inspection-remark span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.inspection-meta dd {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.inspection-remark {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.inspection-remark span {
  display: inline-block;
  margin-right: var(--space-2);
}

.inspection-record table {
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}

.module-state {
  display: grid;
  min-height: 8rem;
  place-items: center;
  margin: 0;
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  color: var(--color-text-muted);
}

.module-state p {
  margin: 0;
}

.module-state--error {
  border-color: var(--color-danger-soft);
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.quality-inspection-create-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
  border-top: 1px solid var(--color-border);
  padding-top: var(--space-5);
}

.quality-inspection-create-form h3,
.quality-inspection-create-form > textarea,
.quality-inspection-create-form > ul,
.quality-inspection-create-form > fieldset,
.quality-inspection-create-form > p {
  grid-column: 1 / -1;
}

.quality-inspection-create-form > label,
.quality-inspection-create-form fieldset label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.quality-inspection-create-form > ul {
  display: grid;
  gap: var(--space-1);
  margin: 0;
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-sm);
  background: var(--color-surface-muted);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.quality-inspection-create-form fieldset {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-3);
  margin: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
}

.quality-inspection-create-form legend {
  padding-inline: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.quality-inspection-create-form fieldset label:last-of-type {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.quality-inspection-create-form > button {
  justify-self: start;
}

.quality-inspection-create-form > p {
  margin: 0;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

@media (max-width: 48rem) {
  .quality-inspection-panel {
    padding: var(--space-4);
  }

  .module-header {
    flex-direction: column;
  }

  .inspection-filter {
    grid-template-columns: 1fr;
  }

  .inspection-record {
    padding: var(--space-4);
  }

  .quality-inspection-create-form,
  .quality-inspection-create-form fieldset {
    grid-template-columns: 1fr;
  }

  .quality-inspection-create-form h3,
  .quality-inspection-create-form > textarea,
  .quality-inspection-create-form > ul,
  .quality-inspection-create-form > fieldset,
  .quality-inspection-create-form > p {
    grid-column: auto;
  }

  .quality-inspection-create-form > button {
    justify-self: stretch;
  }
}
</style>
