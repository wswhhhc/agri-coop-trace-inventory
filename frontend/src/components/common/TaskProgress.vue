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
