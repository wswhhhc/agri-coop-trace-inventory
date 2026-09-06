<script setup lang="ts">
type StatusTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info'

withDefaults(
  defineProps<{
    label: string
    tone?: StatusTone
  }>(),
  {
    tone: 'neutral',
  },
)
</script>

<template>
  <span class="status-badge" :class="`status-badge--${tone}`" role="status">
    {{ label }}
  </span>
</template>

<style scoped>
.status-badge {
  display: inline-flex;
  min-height: 1.75rem;
  align-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  padding: var(--space-1) var(--space-2);
  background: var(--color-surface-muted);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 700;
  line-height: var(--line-height-tight);
  white-space: nowrap;
}

.status-badge--success { border-color: var(--color-success-soft); background: var(--color-success-soft); color: var(--color-success); }
.status-badge--warning { border-color: var(--color-warning-soft); background: var(--color-warning-soft); color: var(--color-warning); }
.status-badge--danger { border-color: var(--color-danger-soft); background: var(--color-danger-soft); color: var(--color-danger); }
.status-badge--info { border-color: var(--color-info-soft); background: var(--color-info-soft); color: var(--color-info); }

@media (forced-colors: active) {
  .status-badge {
    border: 1px solid CanvasText;
  }
}
</style>
