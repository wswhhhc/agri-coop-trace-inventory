<script setup lang="ts">
type NoticeTone = 'info' | 'success' | 'warning' | 'danger'

withDefaults(
  defineProps<{
    message: string
    tone?: NoticeTone
    dismissible?: boolean
  }>(),
  {
    tone: 'info',
    dismissible: true,
  },
)

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <div class="toast-notice" :class="`toast-notice--${tone}`" :role="tone === 'danger' ? 'alert' : 'status'" aria-live="polite">
    <p>{{ message }}</p>
    <button v-if="dismissible" class="toast-notice__close" type="button" aria-label="关闭提示" @click="emit('close')">
      <span aria-hidden="true">×</span>
    </button>
  </div>
</template>

<style scoped>
.toast-notice {
  position: fixed;
  z-index: 50;
  top: var(--space-5);
  right: var(--space-5);
  display: flex;
  width: min(28rem, calc(100vw - 2rem));
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  border: 1px solid var(--color-info-soft);
  border-left: 4px solid var(--color-info);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-md);
}

.toast-notice p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.toast-notice--success { border-color: var(--color-success-soft); border-left-color: var(--color-success); }
.toast-notice--warning { border-color: var(--color-warning-soft); border-left-color: var(--color-warning); }
.toast-notice--danger { border-color: var(--color-danger-soft); border-left-color: var(--color-danger); }

.toast-notice__close {
  display: grid;
  width: 2rem;
  min-width: 2rem;
  height: 2rem;
  min-height: 2rem;
  place-items: center;
  border: 0;
  padding: 0;
  background: transparent;
  color: var(--color-text-muted);
}

.toast-notice__close:hover:not(:disabled) {
  background: var(--color-surface-muted);
  color: var(--color-text);
}

@media (max-width: 48rem) {
  .toast-notice {
    top: var(--space-3);
    right: var(--space-3);
  }
}

@media (forced-colors: active) {
  .toast-notice {
    border: 1px solid CanvasText;
  }
}
</style>
