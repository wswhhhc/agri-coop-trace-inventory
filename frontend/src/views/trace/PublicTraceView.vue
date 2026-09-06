<script setup lang="ts">
import { useRoute } from 'vue-router'

import { getPublicTrace } from '@/api/public-traceability'
import PageState from '@/components/common/PageState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { usePageData } from '@/composables/usePageData'

const route = useRoute()
const traceCode = String(route.params.traceCode)
const { data, loading, error, loadData } = usePageData(() => getPublicTrace(traceCode), null)

function statusTone(value: string): 'success' | 'warning' | 'danger' | 'info' {
  if (value === 'IN_STOCK' || value === 'PASSED') return 'success'
  if (value === 'EXPIRED' || value === 'FAILED') return 'danger'
  if (value === 'PENDING') return 'warning'
  return 'info'
}
</script>

<template>
  <main class="public-trace-page">
    <p class="public-trace-page__kicker">可信农产信息</p>
    <h1>农产品批次追溯</h1>
    <PageState :loading="loading" :error="error" :empty="!data" empty-message="追溯码无效或已失效" @retry="loadData">
      <template v-if="data">
        <p>追溯码：{{ data.traceCode }}</p>
        <section>
          <h2>产品信息</h2>
          <dl>
            <div><dt>名称</dt><dd>{{ data.product.name }}</dd></div>
            <div><dt>分类</dt><dd>{{ data.product.categoryName }}</dd></div>
            <div><dt>单位</dt><dd>{{ data.product.unit }}</dd></div>
          </dl>
        </section>
        <section>
          <h2>批次信息</h2>
          <dl>
            <div><dt>批次编号</dt><dd>{{ data.batch.batchNo }}</dd></div>
            <div><dt>产地</dt><dd>{{ data.batch.origin }}</dd></div>
            <div><dt>生产日期</dt><dd>{{ data.batch.productionDate }}</dd></div>
            <div><dt>到期日期</dt><dd>{{ data.batch.expiryDate }}</dd></div>
            <div><dt>状态</dt><dd><StatusBadge :label="data.batch.status" :tone="statusTone(data.batch.status)" /></dd></div>
          </dl>
        </section>
        <section v-if="data.latestInspection">
          <h2>最近质检</h2>
          <p>
            {{ data.latestInspection.inspectionDate }}，结论：
            <StatusBadge :label="data.latestInspection.conclusion" :tone="statusTone(data.latestInspection.conclusion)" />
          </p>
          <ul>
            <li v-for="item in data.latestInspection.items" :key="item.name">
              {{ item.name }}：{{ item.value }}{{ item.unit ? ` ${item.unit}` : '' }}，标准：{{ item.standard }}，
              <StatusBadge :label="item.isQualified ? '合格' : '不合格'" :tone="item.isQualified ? 'success' : 'danger'" />
            </li>
          </ul>
        </section>
        <section>
          <h2>流转时间线</h2>
          <ol>
            <li v-for="event in data.timeline" :key="`${event.eventType}-${event.occurredAt}`">
              <time :datetime="event.occurredAt">{{ event.occurredAt }}</time>
              <strong>{{ event.title }}</strong>
              <p>{{ event.description }}</p>
            </li>
          </ol>
        </section>
        <p role="note">{{ data.dataNotice }}</p>
      </template>
    </PageState>
  </main>
</template>

<style scoped>
.public-trace-page {
  width: min(100%, 56rem);
  min-height: 100dvh;
  margin: 0 auto;
  padding: var(--space-8) var(--space-5) var(--space-12);
  background: var(--color-bg);
}

.public-trace-page__kicker {
  margin-bottom: var(--space-2);
  color: var(--color-brand);
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.public-trace-page h1 {
  margin-bottom: var(--space-6);
  font-size: clamp(1.75rem, 5vw, 2.5rem);
}

.public-trace-page > .page-state {
  display: grid;
  gap: var(--space-5);
  place-items: stretch;
  text-align: left;
}

.public-trace-page > .page-state > p:first-child {
  margin: 0;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--space-4);
  color: var(--color-text-muted);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: var(--font-size-sm);
  overflow-wrap: anywhere;
}

.public-trace-page > .page-state > section {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.public-trace-page > .page-state h2 {
  margin-bottom: var(--space-4);
  font-size: var(--font-size-lg);
}

.public-trace-page > .page-state dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
  margin: 0;
}

.public-trace-page > .page-state dl > div {
  display: grid;
  gap: var(--space-1);
}

.public-trace-page > .page-state dt {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.public-trace-page > .page-state dd {
  margin: 0;
  color: var(--color-text-secondary);
  overflow-wrap: anywhere;
}

.public-trace-page > .page-state ul {
  display: grid;
  gap: var(--space-2);
  margin: 0;
  padding-left: var(--space-5);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.public-trace-page > .page-state ol {
  display: grid;
  gap: var(--space-4);
  margin: 0;
  padding-left: var(--space-5);
}

.public-trace-page > .page-state ol li {
  padding-left: var(--space-2);
}

.public-trace-page > .page-state time {
  display: block;
  margin-bottom: var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-variant-numeric: tabular-nums;
}

.public-trace-page > .page-state ol p {
  margin: var(--space-1) 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.public-trace-page > .page-state > p[role='note'] {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: var(--line-height-relaxed);
}

@media (max-width: 48rem) {
  .public-trace-page {
    padding: var(--space-6) var(--space-4) var(--space-10);
  }

  .public-trace-page > .page-state > section {
    padding: var(--space-4);
  }

  .public-trace-page > .page-state dl {
    grid-template-columns: 1fr;
  }
}
</style>
