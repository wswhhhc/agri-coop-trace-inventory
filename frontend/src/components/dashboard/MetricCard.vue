<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  description?: string
  tone?: 'default' | 'success' | 'warning' | 'danger' | 'info'
}>()
</script>

<template>
  <article class="metric-card" :class="tone && tone !== 'default' ? `metric-card--${tone}` : undefined">
    <h3 class="metric-card__label">{{ label }}</h3>
    <p class="metric-card__value">{{ value }}</p>
    <p v-if="description" class="metric-card__description">{{ description }}</p>
  </article>
</template>

<style scoped>
.metric-card {
  position: relative;
  display: grid;
  gap: var(--space-2);
  min-width: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  background: var(--color-surface-raised);
}

.metric-card::before {
  position: absolute;
  top: var(--space-4);
  bottom: var(--space-4);
  left: 0;
  width: 3px;
  border-radius: var(--radius-pill);
  background: var(--color-brand);
  content: '';
}

.metric-card__label,
.metric-card__value,
.metric-card__description {
  margin: 0;
}

.metric-card__label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.metric-card__value {
  color: var(--color-text);
  font-size: clamp(1.5rem, 3vw, 2rem);
  font-variant-numeric: tabular-nums;
  font-weight: 750;
  line-height: var(--line-height-tight);
}

.metric-card__description {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.metric-card--success::before { background: var(--color-success); }
.metric-card--warning::before { background: var(--color-warning); }
.metric-card--danger::before { background: var(--color-danger); }
.metric-card--info::before { background: var(--color-info); }

@media (forced-colors: active) {
  .metric-card {
    border: 1px solid CanvasText;
  }

  .metric-card::before {
    background: CanvasText;
  }
}
</style>
