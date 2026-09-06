<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { downloadExportFile, getExportTask, submitExportTask } from '@/api/export'
import { listWarehouses } from '@/api/warehouses'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import TaskProgress from '@/components/common/TaskProgress.vue'
import { usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import type { TaskSummary } from '@/types/resources'
import { getApiErrorMessage } from '@/utils/api-error'

const authStore = useAuthStore()
const warehouseState = usePageData(listWarehouses, [])
const canExport = computed(
  () =>
    authStore.role === 'COOPERATIVE_ADMIN' &&
    authStore.hasPermission(form.reportType === 'INVENTORY_DETAIL' ? 'inventory:read' : 'alert:read'),
)
const submitting = ref(false)
const error = ref('')
const task = ref<TaskSummary | null>(null)
const downloading = ref(false)
const downloadError = ref('')
const form = reactive({
  reportType: 'INVENTORY_DETAIL' as 'INVENTORY_DETAIL' | 'ALERT_DETAIL',
  warehouseId: '',
  startDate: '',
  endDate: '',
})

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds))
}

async function handleSubmit(): Promise<void> {
  submitting.value = true
  error.value = ''
  task.value = null
  try {
    task.value = await submitExportTask({
      reportType: form.reportType,
      filters: {
        ...(form.warehouseId ? { warehouseId: form.warehouseId } : {}),
        ...(form.startDate ? { startDate: form.startDate } : {}),
        ...(form.endDate ? { endDate: form.endDate } : {}),
      },
    })
    for (let attempt = 0; attempt < 20; attempt += 1) {
      if (task.value.status === 'SUCCESS' || task.value.status === 'FAILURE') break
      await wait(1000)
      task.value = await getExportTask(task.value.id)
    }
  } catch (reason) {
    error.value = getApiErrorMessage(reason, '导出任务失败')
  } finally {
    submitting.value = false
  }
}

async function handleDownload(): Promise<void> {
  if (!task.value) return
  downloading.value = true
  downloadError.value = ''
  try {
    const blob = await downloadExportFile(task.value.id)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download =
      typeof task.value.resultPayload?.filename === 'string'
        ? task.value.resultPayload.filename
        : 'export.xlsx'
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (reason) {
    downloadError.value = getApiErrorMessage(reason, '导出文件下载失败')
  } finally {
    downloading.value = false
  }
}
</script>

<template>
  <section class="export-page">
    <PageHeader title="报表导出" description="按条件生成库存或预警明细报表。" />
    <PageContext />
    <p v-if="!canExport" role="alert">仅合作社管理员可以生成报表。</p>
    <form v-else @submit.prevent="handleSubmit">
      <label>
        报表类型
        <select v-model="form.reportType">
          <option value="INVENTORY_DETAIL">库存明细</option>
          <option value="ALERT_DETAIL">预警明细</option>
        </select>
      </label>
      <label>
        仓库
        <select v-model="form.warehouseId">
          <option value="">全部仓库</option>
          <option v-for="warehouse in warehouseState.data" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}
          </option>
        </select>
      </label>
      <label>开始日期 <input v-model="form.startDate" type="date" /></label>
      <label>结束日期 <input v-model="form.endDate" type="date" /></label>
      <button type="submit" :disabled="submitting">{{ submitting ? '生成中…' : '生成报表' }}</button>
    </form>
    <TaskProgress v-if="task" label="导出任务" :status="task.status" :progress="task.progress" />
    <button
      v-if="task?.status === 'SUCCESS'"
      type="button"
      :disabled="downloading"
      @click="handleDownload"
    >
      {{ downloading ? '下载中…' : '下载文件' }}
    </button>
    <p v-if="task?.errorMessage" role="alert">{{ task.errorMessage }}</p>
    <p v-if="error" role="alert">{{ error }}</p>
    <p v-if="downloadError" role="alert">{{ downloadError }}</p>
  </section>
</template>
