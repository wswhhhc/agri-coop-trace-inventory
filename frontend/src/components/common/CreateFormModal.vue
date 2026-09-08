<script setup lang="ts">
import ModalShell from './ModalShell.vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    submitting?: boolean
    error?: string
    submitLabel?: string
  }>(),
  {
    submitting: false,
    error: '',
    submitLabel: '创建',
  },
)

const emit = defineEmits<{
  close: []
  submit: []
}>()

function handleClose(): void {
  if (!props.submitting) emit('close')
}
</script>

<template>
  <ModalShell :open="props.open" :title="props.title" @close="handleClose">
    <form class="create-form-modal" @submit.prevent="emit('submit')">
      <div class="create-form-modal__fields">
        <slot />
      </div>
      <p v-if="props.error" class="create-form-modal__error" role="alert">
        {{ props.error }}
      </p>
      <slot name="status" />
      <div class="create-form-modal__actions">
        <button type="submit" :disabled="props.submitting">
          {{ props.submitting ? '提交中…' : props.submitLabel }}
        </button>
        <button type="button" :disabled="props.submitting" @click="handleClose">取消</button>
      </div>
    </form>
  </ModalShell>
</template>

<style scoped>
.create-form-modal {
  display: grid;
  gap: var(--space-4);
}

.create-form-modal__fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.create-form-modal__fields :deep(label),
.create-form-modal__fields :deep(.generated-code-field) {
  display: grid;
  align-content: start;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.create-form-modal__error {
  margin: 0;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

.create-form-modal__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.create-form-modal__actions button[type='button'] {
  border-color: var(--color-border-strong);
  background: var(--color-surface);
  color: var(--color-text-secondary);
}

.create-form-modal__actions button[type='button']:hover:not(:disabled) {
  background: var(--color-surface-muted);
}

@media (max-width: 48rem) {
  .create-form-modal__fields {
    grid-template-columns: 1fr;
  }

  .create-form-modal__actions {
    flex-direction: column-reverse;
  }

  .create-form-modal__actions button {
    width: 100%;
  }
}
</style>
