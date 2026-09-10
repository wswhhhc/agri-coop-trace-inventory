<script setup lang="ts">
import { computed, ref } from 'vue'

import { getAuditLog, listAuditLogsPage, type AuditLogListParams } from '@/api/audit-logs'
import { listUsers } from '@/api/users'
import FilterBar from '@/components/common/FilterBar.vue'
import PageState from '@/components/common/PageState.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import SelectField, { type SelectFieldOption } from '@/components/common/SelectField.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useFilteredPaginatedList, usePageData } from '@/composables/usePageData'
import type { AuditLogSummary } from '@/types/resources'
import { getApiErrorMessage } from '@/utils/api-error'
import { formatAuditDateTime, formatAuditResult } from '@/utils/audit-format'

type AuditLogFilterState = Pick<
  AuditLogListParams,
  'userId' | 'action' | 'resourceType' | 'resourceId' | 'result' | 'startDate' | 'endDate'
> & {
  userId: string
  action: string
  resourceType: string
  resourceId: string
  result: '' | 'SUCCESS' | 'FAILURE'
  startDate: string
  endDate: string
}
const auditLogList = useFilteredPaginatedList(
  (params) => listAuditLogsPage({
    ...params,
    userId: params.userId || undefined,
    action: params.action || undefined,
    resourceType: params.resourceType || undefined,
    resourceId: params.resourceId || undefined,
    result: params.result || undefined,
    startDate: params.startDate ? toApiDateTime(params.startDate) : undefined,
    endDate: params.endDate ? toApiDateTime(params.endDate) : undefined,
  }),
  {
    userId: '',
    action: '',
    resourceType: '',
    resourceId: '',
    result: '',
    startDate: '',
    endDate: '',
  } satisfies AuditLogFilterState,
)
const userState = usePageData(() => listUsers({ pageSize: 100 }), [])
const userOptions = computed<SelectFieldOption[]>(() => [
  { value: '', label: '全部用户' },
  ...userState.data.map((user) => ({
    value: user.id,
    label: `${user.displayName}（${user.username}）`,
  })),
])
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
    <FilterBar @submit="auditLogList.applyFilters" @reset="auditLogList.resetFilters">
      <label>
        用户
        <SelectField v-model="auditLogList.filters.userId" :options="userOptions" />
      </label>
      <label>操作 <input v-model="auditLogList.filters.action" placeholder="如 CREATE_BATCH" /></label>
      <label>资源类型 <input v-model="auditLogList.filters.resourceType" placeholder="如 BATCH" /></label>
      <label>资源 ID <input v-model="auditLogList.filters.resourceId" /></label>
      <label>
        结果
        <select v-model="auditLogList.filters.result">
          <option value="">全部</option>
          <option value="SUCCESS">成功</option>
          <option value="FAILURE">失败</option>
        </select>
      </label>
      <label>开始时间 <input v-model="auditLogList.filters.startDate" type="datetime-local" /></label>
      <label>结束时间 <input v-model="auditLogList.filters.endDate" type="datetime-local" /></label>
    </FilterBar>
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
            <td>{{ formatAuditDateTime(item.createdAt) }}</td>
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

.audit-log-list-page > .page-state {
  overflow-x: auto;
}

.audit-log-list-page > .page-state table {
  min-width: 62rem;
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

}
</style>
