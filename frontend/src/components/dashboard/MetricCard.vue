<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  description?: string
}>()
</script>

<template>
  <article class="metric-card">
    <h3 class="metric-card__label">{{ label }}</h3>
    <p class="metric-card__value">{{ value }}</p>
    <p v-if="description" class="metric-card__description">{{ description }}</p>
  </article>
</template>
