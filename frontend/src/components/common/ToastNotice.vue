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
