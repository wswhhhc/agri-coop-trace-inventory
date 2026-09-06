<script setup lang="ts">
import { reactive, ref } from 'vue'

import {
  createQualityInspection,
  listQualityInspections,
  type InspectionConclusion,
  type QualityInspectionItemCreatePayload,
} from '@/api/quality-inspections'
import { uploadFile } from '@/api/files'
import { useListPage } from '@/composables/usePageData'
import { getApiErrorMessage } from '@/utils/api-error'

const props = defineProps<{
  batchId: string
  canManage: boolean
}>()

const { items, loading, error, loadData } = useListPage(() => listQualityInspections(props.batchId))
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
  <section class="quality-inspection-panel">
    <h2>质检记录</h2>
    <section v-if="loading" role="status"><p>质检记录加载中…</p></section>
    <section v-else-if="error" role="alert">
      <p>{{ error }}</p>
      <button type="button" @click="loadData">重试</button>
    </section>
    <p v-else-if="items.length === 0">暂无质检记录。</p>
    <article v-for="inspection in items" :key="inspection.id">
      <h3>{{ inspection.inspectionNo }}：{{ inspection.conclusion }}</h3>
      <p>日期：{{ inspection.inspectionDate }}；检验人：{{ inspection.inspectorName }}</p>
      <p v-if="inspection.remarks">备注：{{ inspection.remarks }}</p>
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
            <td>{{ item.isQualified ? '合格' : '不合格' }}</td>
          </tr>
        </tbody>
      </table>
    </article>

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
