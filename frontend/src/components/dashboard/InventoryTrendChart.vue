<script setup lang="ts">
import { computed } from 'vue'

import type { InventoryTrend } from '@/types/dashboard'
import { formatDashboardNumber } from '@/utils/dashboard-format'

const props = defineProps<{
  items: InventoryTrend[]
}>()

const chart = computed(() => {
  const width = 720
  const height = 240
  const left = 48
  const right = 16
  const top = 22
  const bottom = 32
  const plotWidth = width - left - right
  const plotHeight = height - top - bottom

  const groups = new Map<string, InventoryTrend[]>()
  for (const item of props.items) {
    const group = groups.get(item.unit) ?? []
    group.push(item)
    groups.set(item.unit, group)
  }

  return Array.from(groups, ([unit, groupItems]) => {
    const items = [...groupItems].sort((a, b) => a.date.localeCompare(b.date))
    const maximum = Math.max(
      1,
      ...items.flatMap((item) => [item.inboundQuantity, item.outboundQuantity, item.endingQuantity]),
    )
    const x = (index: number) =>
      left + (items.length <= 1 ? plotWidth / 2 : (index / (items.length - 1)) * plotWidth)
    const y = (value: number) => top + ((maximum - value) / maximum) * plotHeight
    const points = items.map((item, index) => ({
      ...item,
      x: x(index),
      inboundY: y(item.inboundQuantity),
      outboundY: y(item.outboundQuantity),
      endingY: y(item.endingQuantity),
      labelVisible:
        index === 0 || index === items.length - 1 || index === Math.floor(items.length / 2),
    }))

    return {
      unit,
      maximum,
      midline: y(maximum / 2),
      baseline: y(0),
      points,
      endingPoints: points.map((point) => String(point.x) + ',' + String(point.endingY)).join(' '),
    }
  })
})
</script>

<template>
  <section v-if="chart.length" class="inventory-trend-chart" aria-labelledby="inventory-trend-chart-title">
    <header class="inventory-trend-chart__header">
      <h3 id="inventory-trend-chart-title">库存收发趋势</h3>
      <div class="inventory-trend-chart__legend" aria-label="图例">
        <span><i class="inventory-trend-chart__legend-bar inventory-trend-chart__legend-bar--inbound" aria-hidden="true"></i>入库</span>
        <span><i class="inventory-trend-chart__legend-bar inventory-trend-chart__legend-bar--outbound" aria-hidden="true"></i>出库</span>
        <span><i class="inventory-trend-chart__legend-line" aria-hidden="true"></i>期末库存</span>
      </div>
    </header>

    <div class="inventory-trend-chart__groups">
      <section v-for="group in chart" :key="group.unit" class="inventory-trend-chart__group">
        <h4>{{ group.unit }}</h4>
        <svg
          :viewBox="'0 0 720 240'"
          role="img"
          :aria-label="group.unit + '库存收发和期末库存趋势'"
        >
          <line x1="48" :y1="group.midline" x2="704" :y2="group.midline" class="inventory-trend-chart__grid" />
          <line x1="48" :y1="group.baseline" x2="704" :y2="group.baseline" class="inventory-trend-chart__grid" />
          <text x="4" y="26" class="inventory-trend-chart__axis-label">{{ formatDashboardNumber(group.maximum) }}</text>
          <text x="18" :y="group.baseline + 4" class="inventory-trend-chart__axis-label">0</text>
          <g v-for="point in group.points" :key="point.date + '-' + point.unit">
            <rect
              :x="point.x - 8"
              :y="point.inboundY"
              width="6"
              :height="group.baseline - point.inboundY"
              class="inventory-trend-chart__bar inventory-trend-chart__bar--inbound"
            />
            <rect
              :x="point.x + 2"
              :y="point.outboundY"
              width="6"
              :height="group.baseline - point.outboundY"
              class="inventory-trend-chart__bar inventory-trend-chart__bar--outbound"
            />
            <text v-if="point.labelVisible" :x="point.x" y="232" text-anchor="middle" class="inventory-trend-chart__date-label">
              {{ point.date.slice(5) }}
            </text>
          </g>
          <polyline :points="group.endingPoints" class="inventory-trend-chart__line" />
        </svg>
      </section>
    </div>
    <p class="inventory-trend-chart__note">同一图中仅比较相同计量单位；详细数值见下方明细表。</p>
  </section>
</template>

<style scoped>
.inventory-trend-chart {
  display: grid;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  background: var(--color-surface-muted);
}

.inventory-trend-chart__header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
}

.inventory-trend-chart__header h3,
.inventory-trend-chart__group h4 {
  margin: 0;
  font-size: var(--font-size-md);
}

.inventory-trend-chart__legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.inventory-trend-chart__legend span {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.inventory-trend-chart__legend-bar,
.inventory-trend-chart__legend-line {
  display: inline-block;
  width: 0.75rem;
  height: 0.75rem;
  border-radius: var(--radius-sm);
  background: var(--color-brand);
}

.inventory-trend-chart__legend-bar--outbound {
  background: var(--color-accent);
}

.inventory-trend-chart__legend-line {
  width: 1rem;
  height: 0.2rem;
  border-radius: var(--radius-pill);
  background: var(--color-text-secondary);
}

.inventory-trend-chart__groups {
  display: grid;
  gap: var(--space-4);
}

.inventory-trend-chart__group {
  min-width: 0;
}

.inventory-trend-chart__group h4 {
  margin-bottom: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.inventory-trend-chart svg {
  display: block;
  width: 100%;
  min-width: 34rem;
  height: auto;
}

.inventory-trend-chart__grid {
  stroke: var(--color-border-strong);
  stroke-dasharray: 3 4;
  stroke-width: 1;
}

.inventory-trend-chart__bar {
  rx: 2;
}

.inventory-trend-chart__bar--inbound {
  fill: var(--color-brand);
}

.inventory-trend-chart__bar--outbound {
  fill: var(--color-accent);
}

.inventory-trend-chart__line {
  fill: none;
  stroke: var(--color-text-secondary);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2.5;
}

.inventory-trend-chart__axis-label,
.inventory-trend-chart__date-label {
  fill: var(--color-text-muted);
  font-size: 10px;
}

.inventory-trend-chart__date-label {
  font-size: 11px;
}

.inventory-trend-chart__note {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

@media (forced-colors: active) {
  .inventory-trend-chart {
    border: 1px solid CanvasText;
  }
}
</style>
