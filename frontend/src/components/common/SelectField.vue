<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

export interface SelectFieldOption {
  value: string
  label: string
  disabled?: boolean
}

const MAX_VISIBLE_OPTIONS = 10
const OPTION_HEIGHT_REM = 2.75

const props = withDefaults(
  defineProps<{
    modelValue: string
    options: SelectFieldOption[]
    name?: string
    required?: boolean
    disabled?: boolean
    placeholder?: string
  }>(),
  {
    name: undefined,
    required: false,
    disabled: false,
    placeholder: '请选择',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const rootRef = ref<HTMLElement | null>(null)
const triggerRef = ref<HTMLButtonElement | null>(null)
const optionRefs = ref<Array<HTMLButtonElement | null>>([])
const open = ref(false)
const activeIndex = ref(-1)
const selectedOption = computed(() => props.options.find((option) => option.value === props.modelValue))
const displayLabel = computed(() => selectedOption.value?.label ?? props.placeholder)
const enabledIndexes = computed(() =>
  props.options.reduce<number[]>((indexes, option, index) => {
    if (!option.disabled) indexes.push(index)
    return indexes
  }, []),
)
const optionsStyle = {
  maxHeight: `${MAX_VISIBLE_OPTIONS * OPTION_HEIGHT_REM}rem`,
}

function focusActiveOption(): void {
  void nextTick(() => optionRefs.value[activeIndex.value]?.focus())
}

function openOptions(): void {
  if (props.disabled || open.value) return
  const selectedIndex = props.options.findIndex((option) => option.value === props.modelValue)
  activeIndex.value = enabledIndexes.value.includes(selectedIndex)
    ? selectedIndex
    : (enabledIndexes.value[0] ?? -1)
  open.value = true
  focusActiveOption()
}

function closeOptions(restoreFocus = true): void {
  open.value = false
  if (restoreFocus) triggerRef.value?.focus()
}

function selectOption(option: SelectFieldOption): void {
  if (option.disabled) return
  emit('update:modelValue', option.value)
  closeOptions()
}

function moveActiveOption(direction: 1 | -1): void {
  const indexes = enabledIndexes.value
  if (indexes.length === 0) return
  const currentPosition = Math.max(0, indexes.indexOf(activeIndex.value))
  const nextPosition = (currentPosition + direction + indexes.length) % indexes.length
  activeIndex.value = indexes[nextPosition]
  focusActiveOption()
}

function handleTriggerKeydown(event: KeyboardEvent): void {
  if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    openOptions()
  }
}

function handleOptionKeydown(event: KeyboardEvent, index: number): void {
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    activeIndex.value = index
    moveActiveOption(event.key === 'ArrowDown' ? 1 : -1)
  } else if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    selectOption(props.options[index])
  } else if (event.key === 'Escape') {
    event.preventDefault()
    closeOptions()
  }
}

function setOptionRef(element: Element | null, index: number): void {
  optionRefs.value[index] = element as HTMLButtonElement | null
}

function handleDocumentPointerDown(event: PointerEvent): void {
  if (open.value && !rootRef.value?.contains(event.target as Node)) closeOptions(false)
}

onMounted(() => document.addEventListener('pointerdown', handleDocumentPointerDown))
onBeforeUnmount(() => document.removeEventListener('pointerdown', handleDocumentPointerDown))
</script>

<template>
  <div ref="rootRef" class="select-field">
    <input
      v-if="props.name && props.required"
      class="select-field__validation"
      type="text"
      :name="props.name"
      :value="props.modelValue"
      required
      tabindex="-1"
      aria-hidden="true"
    />
    <input v-else-if="props.name" type="hidden" :name="props.name" :value="props.modelValue" />
    <button
      ref="triggerRef"
      class="select-field__trigger"
      type="button"
      aria-haspopup="listbox"
      :aria-expanded="open"
      :aria-required="props.required"
      :disabled="props.disabled"
      @click="open ? closeOptions() : openOptions()"
      @keydown="handleTriggerKeydown"
    >
      <span :class="{ 'select-field__placeholder': !selectedOption }">{{ displayLabel }}</span>
      <span class="select-field__arrow" aria-hidden="true">⌄</span>
    </button>
    <div
      v-if="open"
      class="select-field__options"
      role="listbox"
      :style="optionsStyle"
      tabindex="-1"
      @keydown.esc="closeOptions"
    >
      <button
        v-for="(option, index) in props.options"
        :key="option.value || `option-${index}`"
        :ref="(element) => setOptionRef(element as Element | null, index)"
        class="select-field__option"
        :class="{ 'select-field__option--active': index === activeIndex }"
        type="button"
        role="option"
        :aria-selected="option.value === props.modelValue"
        :disabled="option.disabled"
        @click="selectOption(option)"
        @keydown="handleOptionKeydown($event, index)"
      >
        {{ option.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.select-field {
  position: relative;
  width: 100%;
}

.select-field__validation {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  opacity: 0;
  pointer-events: none;
}

.select-field__trigger {
  display: flex;
  width: 100%;
  min-height: 2.75rem;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  border-color: var(--color-border-strong);
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface);
  color: var(--color-text);
  font-weight: 400;
  text-align: left;
}

.select-field__trigger:hover:not(:disabled) {
  border-color: var(--color-brand);
  background: var(--color-surface);
}

.select-field__placeholder {
  color: var(--color-text-muted);
}

.select-field__arrow {
  flex: 0 0 auto;
  color: var(--color-text-secondary);
  font-size: 1.25rem;
  line-height: 1;
}

.select-field__options {
  position: absolute;
  z-index: 20;
  top: calc(100% + var(--space-1));
  right: 0;
  left: 0;
  overflow-y: auto;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-md);
  overscroll-behavior: contain;
}

.select-field__option {
  display: block;
  width: 100%;
  min-height: 2.75rem;
  border: 0;
  border-radius: 0;
  padding: var(--space-2) var(--space-3);
  background: transparent;
  color: var(--color-text);
  font-weight: 400;
  text-align: left;
}

.select-field__option:hover:not(:disabled),
.select-field__option--active:not(:disabled) {
  background: var(--color-brand-soft);
  color: var(--color-brand-900);
}

.select-field__option[aria-selected='true'] {
  font-weight: 600;
}
</style>
