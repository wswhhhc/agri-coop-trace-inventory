<script setup lang="ts">
defineProps<{
  title: string
  description?: string
  eyebrow?: string
}>()
</script>

<template>
  <header class="page-header">
    <div class="page-header__content">
      <p v-if="eyebrow" class="page-header__eyebrow">{{ eyebrow }}</p>
      <h1 class="page-header__title">{{ title }}</h1>
      <p v-if="description" class="page-header__description">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-6);
  margin-bottom: var(--space-6);
}

.page-header__content {
  min-width: 0;
}

.page-header__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-brand);
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-header__title {
  margin-bottom: var(--space-2);
  font-size: clamp(1.5rem, 2vw, var(--font-size-2xl));
}

.page-header__description {
  max-width: 65ch;
  margin-bottom: 0;
  color: var(--color-text-secondary);
}

.page-header__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-2);
}

@media (max-width: 48rem) {
  .page-header {
    align-items: flex-start;
    flex-direction: column;
    gap: var(--space-4);
  }

  .page-header__actions {
    justify-content: flex-start;
  }
}

@media (max-width: 30rem) {
  .page-header__title {
    font-size: var(--font-size-xl);
  }

  .page-header__actions {
    width: 100%;
  }

  .page-header__actions > button {
    flex: 1;
  }
}
</style>
