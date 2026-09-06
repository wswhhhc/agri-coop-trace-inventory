<script setup lang="ts">
import { nextTick, ref, useId, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    description?: string
    confirmText?: string
    cancelText?: string
    tone?: 'default' | 'danger'
  }>(),
  {
    description: '',
    confirmText: '确认',
    cancelText: '取消',
    tone: 'default',
  },
)

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

const dialogRef = ref<HTMLElement | null>(null)
const titleId = useId()

watch(
  () => props.open,
  async (open) => {
    if (open) {
      await nextTick()
      dialogRef.value?.focus()
    }
  },
)
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="confirm-dialog__backdrop" @click.self="emit('cancel')">
      <section
        ref="dialogRef"
        class="confirm-dialog"
        :class="{ 'confirm-dialog--danger': tone === 'danger' }"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        tabindex="-1"
        @keydown.esc="emit('cancel')"
      >
        <h2 :id="titleId">{{ title }}</h2>
        <p v-if="description">{{ description }}</p>
        <div class="confirm-dialog__actions">
          <button type="button" @click="emit('cancel')">{{ cancelText }}</button>
          <button
            type="button"
            :class="{ 'confirm-dialog__confirm--danger': tone === 'danger' }"
            @click="emit('confirm')"
          >
            {{ confirmText }}
          </button>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.confirm-dialog__backdrop {
  position: fixed;
  z-index: 60;
  display: grid;
  inset: 0;
  place-items: center;
  padding: var(--space-5);
  background: var(--color-overlay);
}

.confirm-dialog {
  width: min(100%, 32rem);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-md);
}

.confirm-dialog h2 {
  margin-bottom: var(--space-2);
  font-size: var(--font-size-lg);
}

.confirm-dialog p {
  margin-bottom: var(--space-6);
  color: var(--color-text-secondary);
}

.confirm-dialog__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}

.confirm-dialog__actions button:first-child {
  border-color: var(--color-border-strong);
  background: transparent;
  color: var(--color-text-secondary);
}

.confirm-dialog__confirm--danger {
  background: var(--color-danger);
}

@media (max-width: 48rem) {
  .confirm-dialog {
    padding: var(--space-5);
  }
}

@media (max-width: 30rem) {
  .confirm-dialog__actions {
    width: 100%;
  }

  .confirm-dialog__actions > button {
    flex: 1;
  }
}

@media (forced-colors: active) {
  .confirm-dialog {
    border: 1px solid CanvasText;
  }
}
</style>
