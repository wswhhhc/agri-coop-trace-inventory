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
