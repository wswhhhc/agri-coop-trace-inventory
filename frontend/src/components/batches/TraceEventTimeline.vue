<script setup lang="ts">
import FilterBar from '@/components/common/FilterBar.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import SelectField, { type SelectFieldOption } from '@/components/common/SelectField.vue'
import { listTraceEventsPage, type TraceEventListParams } from '@/api/traceability'
import { useFilteredPaginatedList } from '@/composables/usePageData'
import { formatDateTime } from '@/utils/alerting-format'
import { formatTraceEventType } from '@/utils/traceability-format'

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

const eventIcons: Record<string, string> = {
  PRODUCTION: '产',
  INSPECTION: '检',
  INBOUND: '入',
  OUTBOUND: '出',
  TRANSFER: '调',
  OTHER: '记',
}

function eventIcon(eventType: string): string {
  return eventIcons[eventType] ?? '记'
}
</script>

<template>
  <section class="trace-event-timeline" aria-labelledby="trace-event-title">
    <header class="module-header">
      <div>
        <p class="module-kicker">流转记录</p>
        <h2 id="trace-event-title">追溯时间线</h2>
        <p class="module-description">按发生时间串起生产、质检与库存动作，快速定位批次去向。</p>
      </div>
      <span class="module-count">共 {{ traceList.pagination.totalItems }} 条</span>
    </header>
    <FilterBar class="trace-filter" @submit="traceList.applyFilters" @reset="traceList.resetFilters">
      <label>
        事件类型
        <SelectField v-model="traceList.filters.eventType" :options="eventTypeOptions" />
      </label>
    </FilterBar>
    <section v-if="traceList.loading && traceList.items.length === 0" class="module-state" role="status">
      <p>追溯事件加载中…</p>
    </section>
    <section v-else-if="traceList.error && traceList.items.length === 0" class="module-state module-state--error" role="alert">
      <p>{{ traceList.error }}</p>
      <button type="button" @click="traceList.loadData">重试</button>
    </section>
    <p v-else-if="traceList.items.length === 0" class="module-state">暂无追溯事件。</p>
    <ol v-else class="timeline-list" :aria-busy="traceList.loading">
      <li v-for="event in traceList.items" :key="event.id" class="timeline-item">
        <div class="timeline-marker" aria-hidden="true">{{ eventIcon(event.eventType) }}</div>
        <div class="timeline-entry">
          <div class="timeline-entry__meta">
            <time :datetime="event.eventTime">{{ formatDateTime(event.eventTime) }}</time>
            <span class="event-type">{{ formatTraceEventType(event.eventType) }}</span>
          </div>
          <h3>{{ event.title }}</h3>
          <p v-if="event.description">{{ event.description }}</p>
        </div>
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

.trace-filter {
  grid-template-columns: minmax(15rem, 22rem) auto;
  justify-content: start;
  margin: 0;
  padding: var(--space-3);
  border-color: var(--color-brand-soft);
  background: var(--color-surface-muted);
}

.trace-filter :deep(.filter-bar__actions) {
  align-self: end;
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

.timeline-list {
  display: grid;
  gap: var(--space-4);
  margin: 0;
  padding: 0;
  list-style: none;
}

.timeline-item {
  position: relative;
  display: grid;
  grid-template-columns: 2.75rem minmax(0, 1fr);
  gap: var(--space-4);
  min-width: 0;
}

.timeline-item:not(:last-child)::before {
  content: '';
  position: absolute;
  top: 2.75rem;
  bottom: calc(var(--space-4) * -1);
  left: 1.35rem;
  width: 1px;
  background: var(--color-border-strong);
}

.timeline-marker {
  position: relative;
  z-index: 1;
  display: grid;
  width: 2.75rem;
  height: 2.75rem;
  place-items: center;
  border: 4px solid var(--color-surface);
  border-radius: var(--radius-pill);
  background: var(--color-brand);
  color: var(--color-text-on-brand);
  font-weight: 800;
  box-shadow: 0 0 0 1px var(--color-brand-soft);
}

.timeline-entry {
  min-width: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface-muted);
}

.timeline-entry__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}

.timeline-entry time {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-variant-numeric: tabular-nums;
}

.event-type {
  border-radius: var(--radius-pill);
  padding: 0.15rem var(--space-2);
  background: var(--color-accent-soft);
  color: var(--color-grain-700);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.timeline-entry h3 {
  margin: var(--space-2) 0 var(--space-1);
  font-size: var(--font-size-md);
}

.timeline-entry p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-relaxed);
}

.trace-event-timeline :deep(.pagination-bar) {
  margin-top: var(--space-1);
}

@media (max-width: 48rem) {
  .trace-event-timeline {
    padding: var(--space-4);
  }

  .module-header {
    flex-direction: column;
  }

  .trace-filter {
    grid-template-columns: 1fr;
  }

  .timeline-entry {
    padding-inline: var(--space-4);
  }
}

@media (max-width: 30rem) {
  .timeline-item {
    grid-template-columns: 2.25rem minmax(0, 1fr);
    gap: var(--space-3);
  }

  .timeline-marker {
    width: 2.25rem;
    height: 2.25rem;
  }

  .timeline-item:not(:last-child)::before {
    top: 2.25rem;
    left: 1.1rem;
  }
}
</style>
