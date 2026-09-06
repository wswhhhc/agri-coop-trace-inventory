<script setup lang="ts">
import { reactive, ref } from 'vue'

import { getAuditLog, listAuditLogs } from '@/api/audit-logs'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useListPage } from '@/composables/usePageData'
import type { AuditLogSummary } from '@/types/resources'
import { getApiErrorMessage } from '@/utils/api-error'

const filters = reactive({
  action: '',
  resourceType: '',
  resourceId: '',
  result: '' as '' | 'SUCCESS' | 'FAILURE',
  startDate: '',
  endDate: '',
})
const { items, loading, error, loadData } = useListPage(() =>
  listAuditLogs({
    ...(filters.action ? { action: filters.action.trim() } : {}),
    ...(filters.resourceType ? { resourceType: filters.resourceType.trim() } : {}),
    ...(filters.resourceId ? { resourceId: filters.resourceId.trim() } : {}),
    ...(filters.result ? { result: filters.result } : {}),
    ...(filters.startDate ? { startDate: toApiDateTime(filters.startDate) } : {}),
    ...(filters.endDate ? { endDate: toApiDateTime(filters.endDate) } : {}),
  }),
)
const selectedLog = ref<AuditLogSummary | null>(null)
const detailLoading = ref(false)
const detailError = ref('')

function toApiDateTime(value: string): string {
  return value.length === 16 ? `${value}:00+08:00` : value
}

function resultTone(value: string): 'success' | 'danger' | 'info' {
  if (value === 'SUCCESS') return 'success'
  if (value === 'FAILURE') return 'danger'
  return 'info'
}

function resetFilters(): void {
  filters.action = ''
  filters.resourceType = ''
  filters.resourceId = ''
  filters.result = ''
  filters.startDate = ''
  filters.endDate = ''
  void loadData()
}

async function loadDetail(auditLogId: string): Promise<void> {
  detailLoading.value = true
  detailError.value = ''
  try {
    selectedLog.value = await getAuditLog(auditLogId)
  } catch (reason) {
    detailError.value = getApiErrorMessage(reason, '日志详情加载失败')
  } finally {
    detailLoading.value = false
  }
}
</script>

<template>
  <section class="audit-log-list-page">
    <PageHeader eyebrow="审计追踪" title="操作日志" description="按操作、资源、结果和时间范围查询审计记录。" />
    <PageContext />
    <form class="audit-log-filters" @submit.prevent="loadData">
      <label>操作 <input v-model="filters.action" placeholder="如 CREATE_BATCH" /></label>
      <label>资源类型 <input v-model="filters.resourceType" placeholder="如 BATCH" /></label>
      <label>资源 ID <input v-model="filters.resourceId" /></label>
      <label>
        结果
        <select v-model="filters.result">
          <option value="">全部</option>
          <option value="SUCCESS">成功</option>
          <option value="FAILURE">失败</option>
        </select>
      </label>
      <label>开始时间 <input v-model="filters.startDate" type="datetime-local" /></label>
      <label>结束时间 <input v-model="filters.endDate" type="datetime-local" /></label>
      <button type="submit">查询</button>
      <button type="button" @click="resetFilters">重置</button>
    </form>
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <table>
        <caption>审计日志列表</caption>
        <thead><tr><th scope="col">时间</th><th scope="col">操作</th><th scope="col">模块</th><th scope="col">资源</th><th scope="col">结果</th><th scope="col">操作</th></tr></thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.createdAt }}</td>
            <td>{{ item.action }}</td>
            <td>{{ item.module }}</td>
            <td>{{ item.resourceType }} / {{ item.resourceId || '—' }}</td>
            <td><StatusBadge :label="item.result" :tone="resultTone(item.result)" /></td>
            <td><button type="button" @click="loadDetail(item.id)">查看详情</button></td>
          </tr>
        </tbody>
      </table>
    </PageState>
    <aside v-if="detailLoading || detailError || selectedLog" class="audit-log-detail">
      <h2>日志详情</h2>
      <p v-if="detailLoading">详情加载中…</p>
      <p v-else-if="detailError" role="alert">{{ detailError }}</p>
      <dl v-else-if="selectedLog">
        <div><dt>请求 ID</dt><dd>{{ selectedLog.requestId || '—' }}</dd></div>
        <div><dt>用户 ID</dt><dd>{{ selectedLog.userId || '—' }}</dd></div>
        <div><dt>详情</dt><dd><pre>{{ JSON.stringify(selectedLog.detail, null, 2) }}</pre></dd></div>
      </dl>
    </aside>
  </section>
</template>
