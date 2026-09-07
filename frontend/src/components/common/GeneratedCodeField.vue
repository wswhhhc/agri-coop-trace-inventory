<script setup lang="ts">
defineProps<{
  label: string
  format: string
}>()
</script>

<template>
  <div class="generated-code-field">
    <span class="generated-code-field__label">{{ label }}</span>
    <output class="generated-code-field__value">创建后自动生成</output>
    <span class="generated-code-field__help">格式：{{ format }}</span>
  </div>
</template>

<style scoped>
.generated-code-field {
  display: grid;
  align-content: start;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.generated-code-field__value {
  display: flex;
  align-items: center;
  min-height: 2.75rem;
  box-sizing: border-box;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0 var(--space-3);
  background: var(--color-surface-muted);
  color: var(--color-text-secondary);
  font: inherit;
  font-weight: 500;
}

.generated-code-field__help {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 400;
}
</style>
