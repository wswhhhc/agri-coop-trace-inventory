<script setup lang="ts">
import { computed, toRefs } from 'vue'
import { useRoute } from 'vue-router'

import { getPublicTrace } from '@/api/public-traceability'
import TraceEventList from '@/components/batches/TraceEventList.vue'
import PageState from '@/components/common/PageState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { usePageData } from '@/composables/usePageData'

const route = useRoute()
const traceCode = String(route.params.traceCode)
const pageState = usePageData(() => getPublicTrace(traceCode), null)
const { data, loading, error } = toRefs(pageState)
const { loadData } = pageState
const traceTimeline = computed(() =>
  data.value?.timeline.map((event, index) => ({
    id: `${event.eventType}-${event.occurredAt}-${index}`,
    eventType: event.eventType,
    title: event.title,
    description: event.description,
    eventTime: event.occurredAt,
  })) ?? [],
)

function statusTone(value: string): 'success' | 'warning' | 'danger' | 'info' {
  if (value === 'IN_STOCK' || value === 'PASSED') return 'success'
  if (value === 'EXPIRED' || value === 'FAILED') return 'danger'
  if (value === 'PENDING') return 'warning'
  return 'info'
}

function statusLabel(value: string): string {
  const labels: Record<string, string> = {
    CREATED: '已创建',
    IN_STOCK: '在库',
    OUT_OF_STOCK: '已出库',
    EXPIRED: '已过期',
    PASSED: '合格',
    FAILED: '不合格',
    PENDING: '待处理',
  }
  return labels[value] ?? value
}

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date)
}

function formatDateTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}
</script>

<template>
  <main class="public-trace-page">
    <div class="public-trace-page__glow" aria-hidden="true"></div>

    <div class="public-trace-page__shell">
      <header class="trace-header">
        <div class="trace-header__brand">
          <span class="trace-header__mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M12 20V8.5M12 12.5C8.4 12.5 5.5 10.2 5.5 6.5c3.7 0 6.5 2.3 6.5 6ZM12 16c3.6 0 6.5-2.2 6.5-5.8-3.7 0-6.5 2.2-6.5 5.8Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <span>农业合作社 · 公开信息</span>
        </div>
        <span class="trace-header__secure"><span aria-hidden="true">●</span> 信息已核验</span>
      </header>

      <section class="trace-intro" aria-labelledby="trace-title">
        <p class="trace-intro__eyebrow">PRODUCT PASSPORT / 产品档案</p>
        <h1 id="trace-title">农产品批次追溯</h1>
        <p>从产地到流转，每一批农产品都有迹可循。</p>
      </section>

      <PageState
        :loading="loading"
        :error="error"
        :empty="!data"
        empty-message="追溯码无效或已失效"
        @retry="loadData"
      >
        <template v-if="data">
          <section class="trace-hero" aria-labelledby="product-name">
            <div class="trace-hero__main">
              <div class="product-glyph" aria-hidden="true">农</div>
              <div>
                <p class="section-eyebrow">当前追溯批次</p>
                <h2 id="product-name">{{ data.product.name }}</h2>
                <p class="trace-hero__meta">
                  {{ data.product.categoryName }} <span aria-hidden="true">/</span> {{ data.product.unit }}
                </p>
              </div>
            </div>
            <div class="trace-hero__code">
              <span>追溯码</span>
              <strong>{{ data.traceCode }}</strong>
            </div>
          </section>

          <section class="trace-overview" aria-label="批次关键状态">
            <div class="overview-item overview-item--status">
              <span class="overview-item__label">批次状态</span>
              <StatusBadge :label="statusLabel(data.batch.status)" :tone="statusTone(data.batch.status)" />
            </div>
            <div class="overview-item">
              <span class="overview-item__label">生产日期</span>
              <strong>{{ formatDate(data.batch.productionDate) }}</strong>
            </div>
            <div class="overview-item">
              <span class="overview-item__label">到期日期</span>
              <strong>{{ formatDate(data.batch.expiryDate) }}</strong>
            </div>
            <div class="overview-item">
              <span class="overview-item__label">产地</span>
              <strong>{{ data.batch.origin }}</strong>
            </div>
          </section>

          <div class="trace-layout">
              <section class="trace-card trace-card--batch" aria-labelledby="batch-info-title">
                <div class="trace-card__heading">
                  <div>
                    <p class="section-eyebrow">BATCH DETAILS</p>
                    <h2 id="batch-info-title">批次信息</h2>
                  </div>
                  <span class="trace-card__index">01</span>
                </div>
                <dl class="detail-grid">
                  <div>
                    <dt>批次编号</dt>
                    <dd>{{ data.batch.batchNo }}</dd>
                  </div>
                  <div>
                    <dt>产品单位</dt>
                    <dd>{{ data.product.unit }}</dd>
                  </div>
                  <div>
                    <dt>生产日期</dt>
                    <dd>{{ formatDate(data.batch.productionDate) }}</dd>
                  </div>
                  <div>
                    <dt>到期日期</dt>
                    <dd>{{ formatDate(data.batch.expiryDate) }}</dd>
                  </div>
                  <div class="detail-grid__wide">
                    <dt>产地</dt>
                    <dd>{{ data.batch.origin }}</dd>
                  </div>
                </dl>
                <p v-if="data.product.description" class="product-description">
                  {{ data.product.description }}
                </p>
              </section>

              <section v-if="data.latestInspection" class="trace-card trace-card--wide" aria-labelledby="inspection-title">
                <div class="trace-card__heading">
                  <div>
                    <p class="section-eyebrow">QUALITY CHECK</p>
                    <h2 id="inspection-title">最近质检</h2>
                  </div>
                  <span class="trace-card__index">02</span>
                </div>
                <div class="inspection-result">
                  <div>
                    <span class="inspection-result__label">检验日期</span>
                    <strong>{{ formatDate(data.latestInspection.inspectionDate) }}</strong>
                  </div>
                  <StatusBadge
                    :label="statusLabel(data.latestInspection.conclusion)"
                    :tone="statusTone(data.latestInspection.conclusion)"
                  />
                </div>
                <div class="inspection-list" role="list" aria-label="质检项目">
                  <div v-for="item in data.latestInspection.items" :key="item.name" class="inspection-row" role="listitem">
                    <div class="inspection-row__name">
                      <strong>{{ item.name }}</strong>
                      <span>{{ item.value }}{{ item.unit ? ` ${item.unit}` : '' }}</span>
                    </div>
                    <div class="inspection-row__standard">
                      <span>标准</span>
                      <strong>{{ item.standard }}</strong>
                    </div>
                    <StatusBadge :label="item.isQualified ? '合格' : '不合格'" :tone="item.isQualified ? 'success' : 'danger'" />
                  </div>
                </div>
              </section>

              <section class="trace-card trace-card--wide" aria-labelledby="timeline-title">
                <div class="trace-card__heading">
                  <div>
                    <p class="section-eyebrow">流转记录</p>
                    <h2 id="timeline-title">流转时间线</h2>
                  </div>
                  <span class="trace-timeline__count">共 {{ data.timeline.length }} 条</span>
                </div>
                <TraceEventList :events="traceTimeline" />
              </section>

            <aside class="trace-layout__aside">
              <section class="trust-card" aria-labelledby="trust-title">
                <span class="trust-card__seal" aria-hidden="true">✓</span>
                <p class="section-eyebrow">DATA TRUST</p>
                <h2 id="trust-title">信息可信可查</h2>
                <p>本页面展示该批次公开脱敏信息，内容由系统记录并持续更新。</p>
                <div class="trust-card__line"></div>
                <dl>
                  <div>
                    <dt>最近更新</dt>
                    <dd>{{ formatDateTime(data.updatedAt) }}</dd>
                  </div>
                  <div>
                    <dt>查询凭证</dt>
                    <dd>{{ data.traceCode }}</dd>
                  </div>
                </dl>
              </section>

              <p class="trace-notice" role="note">
                <span aria-hidden="true">ⓘ</span>
                {{ data.dataNotice }}
              </p>
            </aside>
          </div>
        </template>
      </PageState>

      <footer class="trace-footer">公开追溯页 · 让每一次选择都更安心</footer>
    </div>
  </main>
</template>

<style scoped>
.public-trace-page {
  --trace-ink: #18352b;
  --trace-muted: #668075;
  --trace-line: #d9e7df;
  position: relative;
  min-height: 100dvh;
  overflow: hidden;
  background:
    radial-gradient(circle at 76% 4%, rgb(210 236 220 / 68%), transparent 25rem),
    linear-gradient(135deg, #f7fbf7 0%, #eef6f0 48%, #f8faf6 100%);
  color: var(--trace-ink);
}

.public-trace-page__glow {
  position: absolute;
  top: -10rem;
  right: -8rem;
  width: 34rem;
  height: 34rem;
  border: 1px solid rgb(93 150 116 / 14%);
  border-radius: 50%;
  box-shadow: 0 0 0 2.5rem rgb(93 150 116 / 4%), 0 0 0 5rem rgb(93 150 116 / 3%);
  pointer-events: none;
}

.public-trace-page__shell {
  position: relative;
  z-index: 1;
  width: min(100% - 2rem, 76rem);
  margin: 0 auto;
  padding: 1.5rem 0 3rem;
}

.trace-header,
.trace-header__brand,
.trace-header__secure,
.trace-hero,
.trace-hero__main,
.trace-card__heading,
.inspection-result,
.inspection-row {
  display: flex;
  align-items: center;
}

.trace-header {
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: clamp(3.5rem, 9vw, 7rem);
  color: var(--trace-muted);
  font-size: 0.75rem;
  letter-spacing: 0.05em;
}

.trace-header__brand,
.trace-header__secure {
  gap: 0.6rem;
}

.trace-header__brand {
  color: var(--trace-ink);
  font-weight: 750;
}

.trace-header__mark {
  display: grid;
  width: 2rem;
  height: 2rem;
  place-items: center;
  border-radius: 0.7rem;
  background: var(--trace-ink);
  color: #d4eedc;
}

.trace-header__mark svg {
  width: 1.25rem;
  height: 1.25rem;
}

.trace-header__secure {
  color: var(--color-success);
  font-weight: 700;
}

.trace-header__secure span {
  font-size: 0.55rem;
}

.trace-intro {
  max-width: 44rem;
  margin-bottom: 2rem;
}

.trace-intro__eyebrow,
.section-eyebrow {
  margin-bottom: 0.65rem;
  color: var(--color-brand);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.14em;
}

.trace-intro h1 {
  max-width: 20rem;
  margin-bottom: 1rem;
  color: var(--trace-ink);
  font-size: clamp(2.5rem, 6vw, 4.75rem);
  font-weight: 850;
  letter-spacing: -0.065em;
  line-height: 1;
}

.trace-intro > p:last-child {
  margin: 0;
  color: var(--trace-muted);
  font-size: clamp(0.95rem, 2vw, 1.1rem);
}

.trace-hero {
  justify-content: space-between;
  gap: 2rem;
  min-height: 10rem;
  margin-bottom: 1rem;
  border: 1px solid #cfe2d5;
  border-radius: 1.5rem;
  padding: clamp(1.25rem, 4vw, 2rem);
  background: linear-gradient(120deg, #e4f2e8 0%, #f8fcf7 62%, #eef7ed 100%);
  box-shadow: 0 1.25rem 3rem rgb(27 74 49 / 7%);
}

.trace-hero__main {
  gap: 1rem;
  min-width: 0;
}

.product-glyph {
  display: grid;
  flex: 0 0 auto;
  width: 4.25rem;
  height: 4.25rem;
  place-items: center;
  border: 1px solid rgb(42 111 73 / 20%);
  border-radius: 1.25rem;
  background: #cbe8d3;
  color: var(--color-brand-900);
  font-size: 1.55rem;
  font-weight: 850;
}

.trace-hero h2,
.trace-card h2,
.trust-card h2 {
  margin-bottom: 0.35rem;
  color: var(--trace-ink);
  font-size: clamp(1.25rem, 3vw, 1.65rem);
  letter-spacing: -0.035em;
}

.trace-hero h2 {
  overflow-wrap: anywhere;
}

.trace-hero__meta {
  margin: 0;
  color: var(--trace-muted);
  font-size: 0.875rem;
}

.trace-hero__meta span {
  padding: 0 0.35rem;
  color: #94b4a2;
}

.trace-hero__code {
  flex: 0 1 18rem;
  min-width: 0;
  padding-left: 2rem;
  border-left: 1px solid #c8ded0;
}

.trace-hero__code span,
.overview-item__label,
.inspection-result__label,
.inspection-row__standard span,
.trust-card dt {
  display: block;
  color: var(--trace-muted);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.trace-hero__code strong {
  display: block;
  margin-top: 0.35rem;
  color: var(--trace-ink);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 0.82rem;
  overflow-wrap: anywhere;
}

.trace-overview {
  display: grid;
  grid-template-columns: 1.05fr 1fr 1fr 1.3fr;
  gap: 1px;
  overflow: hidden;
  margin-bottom: 1.5rem;
  border: 1px solid var(--trace-line);
  border-radius: 1rem;
  background: var(--trace-line);
}

.overview-item {
  display: grid;
  min-width: 0;
  gap: 0.45rem;
  padding: 1rem 1.15rem;
  background: rgb(255 255 255 / 72%);
}

.overview-item strong {
  color: var(--trace-ink);
  font-size: 0.9rem;
  overflow-wrap: anywhere;
}

.overview-item--status {
  background: #f2fbf4;
}

.trace-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(20rem, 1fr);
  align-items: start;
  gap: 1.5rem;
}

.trace-card--batch {
  grid-column: 1;
  grid-row: 1;
}

.trace-card--wide {
  grid-column: 1 / -1;
  width: 100%;
}

.trace-layout__aside {
  display: grid;
  gap: 1rem;
  min-width: 0;
  grid-column: 2;
  grid-row: 1;
  align-self: start;
}

.trace-card,
.trust-card {
  border: 1px solid var(--trace-line);
  border-radius: 1.25rem;
  background: rgb(255 255 255 / 88%);
  box-shadow: 0 0.75rem 2rem rgb(27 74 49 / 5%);
}

.trace-card {
  padding: clamp(1.25rem, 3vw, 1.75rem);
}

.trace-card__heading {
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.trace-card__heading .section-eyebrow {
  margin-bottom: 0.45rem;
}

.trace-card__heading h2 {
  margin-bottom: 0;
}

.trace-card__index {
  color: #abc8b5;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 0.72rem;
  font-weight: 700;
}

.trace-timeline__count {
  border-radius: 999px;
  padding: 0.35rem 0.75rem;
  background: #d9f1e2;
  color: var(--color-success);
  font-size: 0.8rem;
  font-weight: 800;
  white-space: nowrap;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0;
  margin: 0;
  border-top: 1px solid var(--trace-line);
  border-left: 1px solid var(--trace-line);
}

.detail-grid > div {
  min-width: 0;
  border-right: 1px solid var(--trace-line);
  border-bottom: 1px solid var(--trace-line);
  padding: 0.9rem 1rem;
}

.detail-grid__wide {
  grid-column: 1 / -1;
}

.detail-grid dt {
  margin-bottom: 0.35rem;
  color: var(--trace-muted);
  font-size: 0.72rem;
}

.detail-grid dd {
  margin: 0;
  color: var(--trace-ink);
  font-size: 0.92rem;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.product-description {
  margin: 1.25rem 0 0;
  color: var(--trace-muted);
  font-size: 0.84rem;
  line-height: 1.75;
}

.inspection-result {
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
  border-radius: 0.85rem;
  padding: 0.9rem 1rem;
  background: #f2f8f2;
}

.inspection-result strong {
  display: block;
  margin-top: 0.3rem;
  color: var(--trace-ink);
  font-size: 0.9rem;
}

.inspection-list {
  border-top: 1px solid var(--trace-line);
}

.inspection-row {
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 0;
  border-bottom: 1px solid var(--trace-line);
}

.inspection-row__name,
.inspection-row__standard {
  display: grid;
  gap: 0.25rem;
  min-width: 0;
}

.inspection-row__name {
  flex: 0.9 1 8rem;
}

.inspection-row__standard {
  flex: 1 1 12rem;
}

.inspection-row strong {
  color: var(--trace-ink);
  font-size: 0.85rem;
  overflow-wrap: anywhere;
}

.inspection-row__name span,
.inspection-row__standard strong {
  color: var(--trace-muted);
  font-size: 0.78rem;
  font-weight: 500;
}

.trust-card {
  position: relative;
  overflow: hidden;
  min-height: 0;
  padding: 1.5rem;
  background: var(--trace-ink);
  color: #dceee1;
}

.trust-card::after {
  position: absolute;
  right: -3rem;
  bottom: -4rem;
  width: 10rem;
  height: 10rem;
  border: 1px solid rgb(198 232 207 / 18%);
  border-radius: 50%;
  box-shadow: 0 0 0 1.5rem rgb(198 232 207 / 5%), 0 0 0 3rem rgb(198 232 207 / 4%);
  content: '';
}

.trust-card__seal {
  display: grid;
  width: 2.5rem;
  height: 2.5rem;
  margin-bottom: 2.5rem;
  place-items: center;
  border: 1px solid rgb(198 232 207 / 30%);
  border-radius: 50%;
  color: #c4e9cc;
  font-size: 1.15rem;
}

.trust-card .section-eyebrow {
  color: #a7d6b1;
}

.trust-card h2 {
  color: #f2fbf3;
}

.trust-card > p:not(.section-eyebrow) {
  margin: 0;
  color: #b6d0bd;
  font-size: 0.84rem;
  line-height: 1.7;
}

.trust-card__line {
  height: 1px;
  margin: 1.5rem 0;
  background: rgb(198 232 207 / 20%);
}

.trust-card dl {
  display: grid;
  gap: 1rem;
  margin: 0;
}

.trust-card dd {
  margin: 0.3rem 0 0;
  color: #f2fbf3;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 0.72rem;
  overflow-wrap: anywhere;
}

.trace-notice {
  display: flex;
  gap: 0.55rem;
  margin: 0;
  padding: 0.15rem 0.25rem;
  color: var(--trace-muted);
  font-size: 0.75rem;
  line-height: 1.7;
}

.trace-notice span {
  flex: 0 0 auto;
  color: var(--color-brand);
}

.trace-footer {
  padding-top: 2.5rem;
  color: #89a398;
  font-size: 0.7rem;
  letter-spacing: 0.05em;
  text-align: center;
}

.public-trace-page :deep(.page-state) {
  min-height: 10rem;
  border: 0;
  background: transparent;
  text-align: left;
}

.public-trace-page :deep(.page-state--loading),
.public-trace-page :deep(.page-state--error),
.public-trace-page :deep(.page-state--empty) {
  border: 1px solid var(--trace-line);
  border-radius: 1.25rem;
  background: rgb(255 255 255 / 88%);
  text-align: center;
}

.public-trace-page :deep(.page-state--error) {
  border-color: var(--color-danger-soft);
  background: var(--color-danger-soft);
}

@media (max-width: 50rem) {
  .public-trace-page__shell {
    width: min(100% - 1.5rem, 42rem);
    padding-top: 1rem;
  }

  .trace-header {
    margin-bottom: 4.5rem;
  }

  .trace-layout {
    grid-template-columns: 1fr;
    align-items: start;
  }

  .trace-layout__aside {
    grid-column: 1;
    grid-row: auto;
  }

  .trust-card {
    min-height: 0;
  }

  .trace-card--batch,
  .trace-card--wide {
    grid-column: 1;
    grid-row: auto;
  }

  .trust-card__seal {
    margin-bottom: 1.5rem;
  }
}

@media (max-width: 36rem) {
  .public-trace-page__shell {
    width: min(100% - 1rem, 32rem);
    padding-bottom: 2rem;
  }

  .trace-header {
    align-items: flex-start;
    margin-bottom: 3.5rem;
  }

  .trace-header__secure {
    max-width: 6rem;
    justify-content: flex-end;
    text-align: right;
  }

  .trace-intro h1 {
    font-size: clamp(2.3rem, 13vw, 3.4rem);
  }

  .trace-hero {
    align-items: flex-start;
    flex-direction: column;
    gap: 1.5rem;
  }

  .trace-hero__code {
    width: 100%;
    padding-top: 1rem;
    padding-left: 0;
    border-top: 1px solid #c8ded0;
    border-left: 0;
  }

  .trace-overview {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .overview-item {
    padding: 0.85rem;
  }

  .overview-item strong {
    font-size: 0.82rem;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-grid__wide {
    grid-column: auto;
  }

  .inspection-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 0.75rem;
  }

  .inspection-row__standard {
    grid-column: 1 / -1;
    grid-row: 2;
  }

  .inspection-row > .status-badge {
    grid-column: 2;
    grid-row: 1;
  }
}

@media (prefers-reduced-motion: no-preference) {
  .trace-intro,
  .trace-hero,
  .trace-overview,
  .trace-card,
  .trust-card {
    animation: trace-fade-in 500ms both;
  }

  .trace-hero { animation-delay: 60ms; }
  .trace-overview { animation-delay: 120ms; }
  .trace-card:nth-of-type(2) { animation-delay: 180ms; }
  .trace-card:nth-of-type(3) { animation-delay: 240ms; }
  .trace-layout__aside { animation-delay: 180ms; }
}

@keyframes trace-fade-in {
  from { opacity: 0; transform: translateY(0.6rem); }
  to { opacity: 1; transform: translateY(0); }
}

@media (forced-colors: active) {
  .trace-card,
  .trust-card,
  .trace-hero,
  .trace-overview {
    border: 1px solid CanvasText;
  }
}
</style>
