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
