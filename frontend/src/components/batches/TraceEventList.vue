<script setup lang="ts">
import { formatDateTime } from '@/utils/alerting-format'
import { formatTraceEventType } from '@/utils/traceability-format'

export interface TraceEventListItem {
  id?: string
  eventType: string
  title: string
  description: string | null
  eventTime: string
}

defineProps<{
  events: TraceEventListItem[]
}>()

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
  <p v-if="events.length === 0" class="trace-event-list__empty">暂无追溯记录。</p>
  <ol v-else class="trace-event-list">
    <li
      v-for="event in events"
      :key="event.id ?? `${event.eventType}-${event.eventTime}-${event.title}`"
      class="trace-event-list__item"
    >
      <span class="trace-event-list__marker" aria-hidden="true">{{ eventIcon(event.eventType) }}</span>
      <article class="trace-event-list__card">
        <div class="trace-event-list__meta">
          <time :datetime="event.eventTime">{{ formatDateTime(event.eventTime) }}</time>
          <span>{{ formatTraceEventType(event.eventType) }}</span>
        </div>
        <h3>{{ event.title }}</h3>
        <p v-if="event.description">{{ event.description }}</p>
      </article>
    </li>
  </ol>
</template>

<style scoped>
.trace-event-list {
  position: relative;
  display: grid;
  gap: 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.trace-event-list__item {
  position: relative;
  display: grid;
  grid-template-columns: 2.75rem minmax(0, 1fr);
  gap: 1rem;
  min-width: 0;
}

.trace-event-list__item:not(:last-child)::before {
  position: absolute;
  top: 2.75rem;
  bottom: -1rem;
  left: 1.35rem;
  width: 1px;
  background: var(--trace-line, #d9e7df);
  content: '';
}

.trace-event-list__marker {
  position: relative;
  z-index: 1;
  display: grid;
  width: 2.75rem;
  height: 2.75rem;
  place-items: center;
  border: 4px solid var(--color-surface, #fff);
  border-radius: 50%;
  background: var(--color-brand, #176b4d);
  color: var(--color-text-on-brand, #fff);
  font-size: 1rem;
  font-weight: 800;
  box-shadow: 0 0 0 1px var(--color-brand-soft, #dcefe5);
}

.trace-event-list__card {
  min-width: 0;
  border: 1px solid var(--trace-line, #d9e7df);
  border-radius: 0.75rem;
  padding: 1rem 1.25rem;
  background: var(--color-surface-muted, #eef8f1);
}

.trace-event-list__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.trace-event-list__meta time {
  color: var(--color-text-muted, #6b7c74);
  font-size: 0.75rem;
  font-variant-numeric: tabular-nums;
}

.trace-event-list__meta span {
  border-radius: 999px;
  padding: 0.15rem 0.5rem;
  background: var(--color-accent-soft, #f8edcf);
  color: var(--color-grain-700, #8a6721);
  font-size: 0.75rem;
  font-weight: 700;
}

.trace-event-list__card h3 {
  margin: 0.5rem 0 0.25rem;
  color: var(--color-text, #17231e);
  font-size: 1rem;
}

.trace-event-list__card p {
  margin: 0;
  color: var(--color-text-secondary, #40534b);
  font-size: 0.875rem;
  line-height: 1.65;
}

.trace-event-list__empty {
  margin: 0;
  padding: 2rem 1rem;
  border: 1px dashed var(--color-border-strong, #cbd6d0);
  border-radius: 0.75rem;
  color: var(--color-text-muted, #6b7c74);
  text-align: center;
}

@media (max-width: 30rem) {
  .trace-event-list__item {
    grid-template-columns: 2.25rem minmax(0, 1fr);
    gap: 0.75rem;
  }

  .trace-event-list__item:not(:last-child)::before {
    top: 2.25rem;
    left: 1.1rem;
  }

  .trace-event-list__marker {
    width: 2.25rem;
    height: 2.25rem;
  }

  .trace-event-list__card {
    padding-inline: 1rem;
  }
}
</style>
