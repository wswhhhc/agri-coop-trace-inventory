<script setup lang="ts">
import { computed } from 'vue'

import type { ForecastPointSummary } from '@/types/resources'

const props = defineProps<{
  points: ForecastPointSummary[]
}>()

const chart = computed(() => {
  const width = 640
  const height = 240
  const paddingX = 32
  const paddingY = 24
  const plotHeight = 160
  const plotWidth = width - paddingX * 2
  const values = props.points.flatMap((point) => [point.lowerBound, point.upperBound, point.predictedQuantity])
  const minimum = Math.min(0, ...values)
  const maximum = Math.max(1, ...values)
  const range = maximum - minimum || 1
  const x = (index: number) => paddingX + (props.points.length <= 1 ? plotWidth / 2 : (index / (props.points.length - 1)) * plotWidth)
  const y = (value: number) => paddingY + ((maximum - value) / range) * plotHeight
  const toPoints = (selector: (point: ForecastPointSummary) => number) =>
    props.points.map((point, index) => `${x(index)},${y(selector(point))}`).join(' ')
  const upperPoints = props.points.map((point, index) => `${x(index)},${y(point.upperBound)}`)
  const lowerPoints = props.points.map((point, index) => `${x(index)},${y(point.lowerBound)}`).reverse()

  return {
    predicted: toPoints((point) => point.predictedQuantity),
    band: [...upperPoints, ...lowerPoints].join(' '),
    topLabel: maximum.toFixed(1),
    bottomLabel: minimum.toFixed(1),
    baselineY: y(0),
    points: props.points.map((point, index) => ({ x: x(index), y: y(point.predictedQuantity), label: point.forecastDate })),
    width,
    height,
  }
})
</script>

<template>
  <section class="forecast-range-chart" aria-labelledby="forecast-range-chart-title">
    <header class="forecast-range-chart__header">
      <h3 id="forecast-range-chart-title">预测趋势与区间</h3>
      <div class="forecast-range-chart__legend" aria-label="图例">
        <span><i class="forecast-range-chart__legend-line" aria-hidden="true"></i>预测量</span>
        <span><i class="forecast-range-chart__legend-band" aria-hidden="true"></i>预测区间</span>
      </div>
    </header>
    <svg
      class="forecast-range-chart__svg"
      :viewBox="`0 0 ${chart.width} ${chart.height}`"
      role="img"
      aria-label="预测数量趋势和预测区间"
    >
      <line x1="32" :y1="chart.baselineY" x2="608" :y2="chart.baselineY" class="forecast-range-chart__baseline" />
      <line x1="32" y1="24" x2="608" y2="24" class="forecast-range-chart__grid" />
      <line x1="32" y1="184" x2="608" y2="184" class="forecast-range-chart__grid" />
      <polygon :points="chart.band" class="forecast-range-chart__band" />
      <polyline :points="chart.predicted" class="forecast-range-chart__line" />
      <circle v-for="point in chart.points" :key="point.label" :cx="point.x" :cy="point.y" r="3.5" class="forecast-range-chart__point" />
      <text x="4" y="28" class="forecast-range-chart__label">{{ chart.topLabel }}</text>
      <text x="4" y="188" class="forecast-range-chart__label">{{ chart.bottomLabel }}</text>
    </svg>
    <p class="forecast-range-chart__note">图形用于趋势判断，具体数值请以预测明细表为准。</p>
  </section>
</template>

<style scoped>
.forecast-range-chart {
  display: grid;
  gap: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  background: var(--color-surface-muted);
}

.forecast-range-chart__header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
}

.forecast-range-chart__header h3 {
  margin: 0;
  font-size: var(--font-size-md);
}

.forecast-range-chart__legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.forecast-range-chart__legend span {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.forecast-range-chart__legend-line,
.forecast-range-chart__legend-band {
  display: inline-block;
  width: 1rem;
  height: 0.25rem;
  border-radius: var(--radius-pill);
  background: var(--color-brand);
}

.forecast-range-chart__legend-band {
  height: 0.75rem;
  background: var(--color-brand-soft);
}

.forecast-range-chart__svg {
  display: block;
  width: 100%;
  min-height: 12rem;
  overflow: visible;
}

.forecast-range-chart__grid,
.forecast-range-chart__baseline {
  stroke: var(--color-border);
  stroke-width: 1;
}

.forecast-range-chart__baseline {
  stroke-dasharray: 4 4;
}

.forecast-range-chart__band {
  fill: var(--color-brand-soft);
  opacity: 0.85;
}

.forecast-range-chart__line {
  fill: none;
  stroke: var(--color-brand);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 3;
}

.forecast-range-chart__point {
  fill: var(--color-surface);
  stroke: var(--color-brand);
  stroke-width: 2;
}

.forecast-range-chart__label {
  fill: var(--color-text-muted);
  font-size: 11px;
}

.forecast-range-chart__note {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}
</style>
