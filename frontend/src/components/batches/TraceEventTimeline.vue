<script setup lang="ts">
import { listTraceEvents } from '@/api/traceability'
import { useListPage } from '@/composables/usePageData'

const props = defineProps<{
  batchId: string
}>()

const { items, loading, error, loadData } = useListPage(() => listTraceEvents(props.batchId))
</script>

<template>
  <section class="trace-event-timeline">
    <h2>追溯时间线</h2>
    <section v-if="loading" role="status"><p>追溯事件加载中…</p></section>
    <section v-else-if="error" role="alert">
      <p>{{ error }}</p>
      <button type="button" @click="loadData">重试</button>
    </section>
    <p v-else-if="items.length === 0">暂无追溯事件。</p>
    <ol v-else>
      <li v-for="event in items" :key="event.id">
        <time :datetime="event.eventTime">{{ event.eventTime }}</time>
        <strong>{{ event.title }}</strong>
        <span>（{{ event.eventType }}）</span>
        <p v-if="event.description">{{ event.description }}</p>
      </li>
    </ol>
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
