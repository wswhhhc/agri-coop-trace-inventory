<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    showReset?: boolean
    submitLabel?: string
    resetLabel?: string
  }>(),
  {
    showReset: true,
    submitLabel: '查询',
    resetLabel: '重置',
  },
)

const emit = defineEmits<{
  submit: []
  reset: []
}>()
</script>

<template>
  <form class="filter-bar" @submit.prevent="emit('submit')">
    <slot />
    <div class="filter-bar__actions">
      <button type="submit">{{ props.submitLabel }}</button>
      <button v-if="props.showReset" class="filter-bar__reset" type="button" @click="emit('reset')">
        {{ props.resetLabel }}
      </button>
    </div>
  </form>
</template>

<style scoped>
.filter-bar {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: end;
  gap: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  background: var(--color-surface-muted);
}

.filter-bar :deep(label) {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.filter-bar__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.filter-bar__reset {
  border-color: var(--color-border-strong);
  background: transparent;
  color: var(--color-text-secondary);
}

@media (max-width: 48rem) {
  .filter-bar {
    grid-template-columns: 1fr;
  }

  .filter-bar__actions button {
    flex: 1 1 8rem;
  }
}
</style>
