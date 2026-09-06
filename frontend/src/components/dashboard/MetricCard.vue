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
