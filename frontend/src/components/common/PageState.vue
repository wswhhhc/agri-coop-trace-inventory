<script setup lang="ts">
withDefaults(
  defineProps<{
    loading?: boolean
    error?: string
    empty?: boolean
    emptyMessage?: string
  }>(),
  {
    loading: false,
    error: '',
    empty: false,
    emptyMessage: '暂无数据',
  },
)

const emit = defineEmits<{
  retry: []
}>()
</script>

<template>
  <section v-if="loading" class="page-state page-state--loading" role="status" aria-live="polite">
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
