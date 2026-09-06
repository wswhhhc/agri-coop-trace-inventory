<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string
    status: string
    progress?: number
  }>(),
  {
    progress: 0,
  },
)
</script>

<template>
  <section class="task-progress" role="status" aria-live="polite">
    <div class="task-progress__header">
      <strong>{{ label }}</strong>
      <span>{{ status }}</span>
    </div>
    <div class="task-progress__track" role="progressbar" :aria-valuenow="progress" aria-valuemin="0" aria-valuemax="100">
      <span class="task-progress__value" :style="{ width: `${Math.min(100, Math.max(0, progress))}%` }"></span>
    </div>
    <small>{{ progress }}%</small>
  </section>
</template>

<style scoped>
.task-progress {
  display: grid;
  gap: var(--space-2);
  margin-block: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  background: var(--color-surface-muted);
}

.task-progress__header {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.task-progress__header span,
.task-progress small {
  color: var(--color-text-muted);
}

.task-progress__track {
  height: 0.5rem;
  overflow: hidden;
  border-radius: var(--radius-pill);
  background: var(--color-border);
}

.task-progress__value {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--color-brand);
  transition: width var(--duration-normal) var(--ease-standard);
}

@media (max-width: 30rem) {
  .task-progress__header {
    align-items: flex-start;
    flex-direction: column;
    gap: var(--space-1);
  }
}
</style>
