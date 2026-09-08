<script setup lang="ts">
import { nextTick, ref, useId, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    closeLabel?: string
  }>(),
  {
    closeLabel: '关闭弹窗',
  },
)

const emit = defineEmits<{
  close: []
}>()

const dialogRef = ref<HTMLElement | null>(null)
const titleId = useId()

watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen) {
      await nextTick()
      dialogRef.value?.focus()
    }
  },
)
</script>

<template>
  <Teleport to="body">
    <div
      v-if="props.open"
      class="modal-shell__backdrop"
      data-modal-backdrop
      @click.self="emit('close')"
    >
      <section
        ref="dialogRef"
        class="modal-shell"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        tabindex="-1"
        @keydown.esc="emit('close')"
      >
        <header class="modal-shell__header">
          <h2 :id="titleId">{{ props.title }}</h2>
          <button
            class="modal-shell__close"
            type="button"
            :aria-label="props.closeLabel"
            @click="emit('close')"
          >
            ×
          </button>
        </header>
        <div class="modal-shell__body">
          <slot />
        </div>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-shell__backdrop {
  position: fixed;
  z-index: 60;
  display: grid;
  inset: 0;
  place-items: center;
  overflow-y: auto;
  padding: var(--space-5);
  background: var(--color-overlay);
}

.modal-shell {
  width: min(100%, 48rem);
  max-height: calc(100dvh - 2 * var(--space-5));
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-md);
}

.modal-shell__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  padding: var(--space-5) var(--space-6);
}

.modal-shell__header h2 {
  margin: 0;
  font-size: var(--font-size-lg);
}

.modal-shell__close {
  display: grid;
  width: 2.25rem;
  min-height: 2.25rem;
  flex: 0 0 auto;
  place-items: center;
  margin: -0.25rem -0.5rem 0 0;
  border-color: transparent;
  padding: 0;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 1.5rem;
  line-height: 1;
}

.modal-shell__close:hover:not(:disabled) {
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.modal-shell__body {
  max-height: calc(100dvh - 7rem);
  overflow-y: auto;
  padding: var(--space-6);
}

@media (max-width: 48rem) {
  .modal-shell__backdrop {
    align-items: end;
    padding: var(--space-3);
  }

  .modal-shell {
    max-height: calc(100dvh - 2 * var(--space-3));
  }

  .modal-shell__header,
  .modal-shell__body {
    padding: var(--space-4);
  }

  .modal-shell__body {
    max-height: calc(100dvh - 6rem);
  }
}

@media (forced-colors: active) {
  .modal-shell {
    border: 1px solid CanvasText;
  }
}
</style>
