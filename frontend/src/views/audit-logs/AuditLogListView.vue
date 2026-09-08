<script setup lang="ts">
import { reactive, ref } from 'vue'

import { getAuditLog, listAuditLogsPage } from '@/api/audit-logs'
import PageState from '@/components/common/PageState.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { usePaginatedList } from '@/composables/usePageData'
import type { AuditLogSummary } from '@/types/resources'
import { getApiErrorMessage } from '@/utils/api-error'
import { formatAuditResult } from '@/utils/audit-format'

const filters = reactive({
  action: '',
  resourceType: '',
  resourceId: '',
  result: '' as '' | 'SUCCESS' | 'FAILURE',
  startDate: '',
  endDate: '',
})
const auditLogList = usePaginatedList((pagination) =>
  listAuditLogsPage({
    ...pagination,
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
  void auditLogList.loadData(1)
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
    <form class="audit-log-filters" @submit.prevent="() => auditLogList.loadData(1)">
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
    <PageState
      :loading="auditLogList.loading"
      :error="auditLogList.error"
      :empty="auditLogList.items.length === 0"
      @retry="auditLogList.loadData"
    >
      <table>
        <caption>审计日志列表</caption>
        <thead><tr><th scope="col">时间</th><th scope="col">操作</th><th scope="col">模块</th><th scope="col">资源</th><th scope="col">结果</th><th scope="col">操作</th></tr></thead>
        <tbody>
          <tr v-for="item in auditLogList.items" :key="item.id">
            <td>{{ item.createdAt }}</td>
            <td>{{ item.action }}</td>
            <td>{{ item.module }}</td>
            <td>{{ item.resourceType }} / {{ item.resourceId || '—' }}</td>
            <td><StatusBadge :label="formatAuditResult(item.result)" :tone="resultTone(item.result)" /></td>
            <td><button type="button" @click="loadDetail(item.id)">查看详情</button></td>
          </tr>
        </tbody>
      </table>
    </PageState>
    <PaginationBar
      :page="auditLogList.pagination.page"
      :total-pages="auditLogList.pagination.totalPages"
      :total-items="auditLogList.pagination.totalItems"
      :page-size="auditLogList.pagination.pageSize"
      @change="auditLogList.goToPage"
      @page-size-change="auditLogList.setPageSize"
    />
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

<style scoped>
.audit-log-list-page {
  display: grid;
  gap: var(--space-5);
}

.audit-log-filters {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: end;
  gap: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  background: var(--color-surface-muted);
}

.audit-log-filters > label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.audit-log-list-page > .page-state {
  overflow-x: auto;
}

.audit-log-list-page > .page-state table {
  min-width: 62rem;
}

.audit-log-filters > button:last-child {
  border-color: var(--color-border-strong);
  background: transparent;
  color: var(--color-text-secondary);
}

.audit-log-detail {
  display: grid;
  gap: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.audit-log-detail h2 {
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.audit-log-detail dl {
  display: grid;
  gap: var(--space-2);
  margin: 0;
}

.audit-log-detail dl > div {
  display: grid;
  grid-template-columns: minmax(6rem, 0.35fr) minmax(0, 1fr);
  gap: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--space-2);
}

.audit-log-detail dt {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.audit-log-detail dd {
  min-width: 0;
  margin: 0;
  color: var(--color-text-secondary);
  overflow-wrap: anywhere;
}

@media (max-width: 48rem) {
  .audit-log-detail dl > div {
    grid-template-columns: 1fr;
    gap: var(--space-1);
  }

  .audit-log-filters {
    grid-template-columns: 1fr;
  }
}
</style>
