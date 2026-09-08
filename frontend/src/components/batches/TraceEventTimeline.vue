<script setup lang="ts">
import FilterBar from '@/components/common/FilterBar.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import SelectField, { type SelectFieldOption } from '@/components/common/SelectField.vue'
import { listTraceEventsPage, type TraceEventListParams } from '@/api/traceability'
import { useFilteredPaginatedList } from '@/composables/usePageData'

const props = defineProps<{
  batchId: string
}>()

type TraceEventFilterState = Pick<TraceEventListParams, 'eventType'> & { eventType: string }
const traceList = useFilteredPaginatedList(
  (params) => listTraceEventsPage(props.batchId, {
    ...params,
    eventType: params.eventType || undefined,
  }),
  { eventType: '' } satisfies TraceEventFilterState,
)
const eventTypeOptions: SelectFieldOption[] = [
  { value: '', label: '全部事件类型' },
  { value: 'PRODUCTION', label: '生产' },
  { value: 'INSPECTION', label: '质检' },
  { value: 'INBOUND', label: '入库' },
  { value: 'OUTBOUND', label: '出库' },
  { value: 'TRANSFER', label: '调拨' },
  { value: 'OTHER', label: '其他' },
]
</script>

<template>
  <section class="trace-event-timeline">
    <h2>追溯时间线</h2>
    <FilterBar @submit="traceList.applyFilters" @reset="traceList.resetFilters">
      <label>
        事件类型
        <SelectField v-model="traceList.filters.eventType" :options="eventTypeOptions" />
      </label>
    </FilterBar>
    <section v-if="traceList.loading" role="status"><p>追溯事件加载中…</p></section>
    <section v-else-if="traceList.error" role="alert">
      <p>{{ traceList.error }}</p>
      <button type="button" @click="traceList.loadData">重试</button>
    </section>
    <p v-else-if="traceList.items.length === 0">暂无追溯事件。</p>
    <ol v-else>
      <li v-for="event in traceList.items" :key="event.id">
        <time :datetime="event.eventTime">{{ event.eventTime }}</time>
        <strong>{{ event.title }}</strong>
        <span>（{{ event.eventType }}）</span>
        <p v-if="event.description">{{ event.description }}</p>
      </li>
    </ol>
    <PaginationBar
      :page="traceList.pagination.page"
      :total-pages="traceList.pagination.totalPages"
      :total-items="traceList.pagination.totalItems"
      :page-size="traceList.pagination.pageSize"
      @change="traceList.goToPage"
      @page-size-change="traceList.setPageSize"
    />
  </section>
</template>

<style scoped>
.trace-event-timeline {
  display: grid;
  gap: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.trace-event-timeline h2 {
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.trace-event-timeline ol {
  display: grid;
  gap: var(--space-4);
  margin: 0;
  padding: 0 0 0 var(--space-5);
}

.trace-event-timeline li {
  display: grid;
  gap: var(--space-1);
  padding-left: var(--space-2);
}

.trace-event-timeline time {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-variant-numeric: tabular-nums;
}

.trace-event-timeline li strong {
  color: var(--color-text);
}

.trace-event-timeline li p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

@media (max-width: 48rem) {
  .trace-event-timeline {
    padding: var(--space-4);
  }
}
</style>
