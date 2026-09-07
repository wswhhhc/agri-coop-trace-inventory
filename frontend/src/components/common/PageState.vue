<script setup lang="ts">
withDefaults(
  defineProps<{
    loading?: boolean
    error?: string
    empty?: boolean
    emptyMessage?: string
    preserveContentOnLoading?: boolean
  }>(),
  {
    loading: false,
    error: '',
    empty: false,
    emptyMessage: '暂无数据',
    preserveContentOnLoading: false,
  },
)

const emit = defineEmits<{
  retry: []
}>()
</script>

<template>
  <section
    v-if="preserveContentOnLoading"
    class="page-state page-state--content"
    :aria-busy="loading ? 'true' : undefined"
  >
    <slot />
    <div v-if="loading" class="page-state__refreshing" role="status" aria-live="polite">
      加载中…
    </div>
    <div v-else-if="error" class="page-state__refresh-error" role="alert">
      {{ error }}
    </div>
  </section>

  <section v-else-if="loading" class="page-state page-state--loading" role="status" aria-live="polite">
    <div class="page-state__skeleton" aria-hidden="true">
      <span></span>
      <span></span>
      <span></span>
    </div>
    <p class="page-state__message">加载中…</p>
  </section>

  <section v-else-if="error" class="page-state page-state--error" role="alert">
    <p class="page-state__message">{{ error }}</p>
    <button type="button" @click="emit('retry')">重试</button>
  </section>

  <section v-else-if="empty" class="page-state page-state--empty" role="status">
    <span class="page-state__mark" aria-hidden="true">—</span>
    <p class="page-state__message">{{ emptyMessage }}</p>
  </section>

  <slot v-else />
</template>

<style scoped>
.page-state {
  display: grid;
  min-height: 10rem;
  place-items: center;
  gap: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-8);
  background: var(--color-surface);
  text-align: center;
}

.page-state--content {
  position: relative;
  display: block;
  min-height: 36rem;
  border: 0;
  padding: 0;
  background: transparent;
  text-align: left;
}

.page-state__refreshing,
.page-state__refresh-error {
  position: absolute;
  z-index: 1;
  inset: 0;
  display: grid;
  place-items: center;
  padding: var(--space-4);
  background: color-mix(in srgb, var(--color-surface) 78%, transparent);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  pointer-events: none;
}

.page-state__refresh-error {
  background: color-mix(in srgb, var(--color-danger-soft) 86%, transparent);
  color: var(--color-danger);
}

.page-state__message {
  max-width: 45rem;
  margin: 0;
  color: var(--color-text-secondary);
}

.page-state--error {
  border-color: color-mix(in srgb, var(--color-danger) 35%, var(--color-border));
  background: var(--color-danger-soft);
}

.page-state--error .page-state__message {
  color: var(--color-danger);
}

.page-state--empty {
  background: var(--color-surface-muted);
}

.page-state__mark {
  display: grid;
  width: 2.5rem;
  height: 2.5rem;
  place-items: center;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-pill);
  color: var(--color-text-muted);
  font-size: var(--font-size-lg);
}

.page-state__skeleton {
  display: grid;
  width: min(100%, 32rem);
  gap: var(--space-3);
}

.page-state__skeleton span {
  display: block;
  height: 0.875rem;
  border-radius: var(--radius-pill);
  background: linear-gradient(
    90deg,
    var(--color-surface-muted) 0%,
    var(--color-border) 50%,
    var(--color-surface-muted) 100%
  );
  background-size: 200% 100%;
  animation: page-state-shimmer 1.4s var(--ease-standard) infinite;
}

.page-state__skeleton span:nth-child(2) {
  width: 82%;
}

.page-state__skeleton span:nth-child(3) {
  width: 64%;
}

@keyframes page-state-shimmer {
  from {
    background-position: 100% 0;
  }

  to {
    background-position: -100% 0;
  }
}

@media (max-width: 30rem) {
  .page-state {
    min-height: 8rem;
    padding: var(--space-6) var(--space-4);
  }
}

@media (forced-colors: active) {
  .page-state {
    border: 1px solid CanvasText;
  }
}
</style>
