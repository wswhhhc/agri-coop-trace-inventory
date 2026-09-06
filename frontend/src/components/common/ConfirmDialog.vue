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
