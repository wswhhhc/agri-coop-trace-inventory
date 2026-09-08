<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const PAGE_PICKER_SIZE = 10

type PageToken = number | 'ellipsis-start' | 'ellipsis-end'
type EllipsisToken = 'ellipsis-start' | 'ellipsis-end'

const props = withDefaults(
  defineProps<{
    page: number
    totalPages: number
    totalItems: number
    pageSize: number
    pageSizeOptions?: number[]
  }>(),
  {
    pageSizeOptions: () => [10, 20, 50],
  },
)

const emit = defineEmits<{
  change: [page: number]
  'page-size-change': [pageSize: number]
}>()

const pagePickerOpen = ref(false)
const activeEllipsis = ref<EllipsisToken | null>(null)
const pagePickerPage = ref(1)
const pagePickerPageCount = computed(() => Math.ceil(props.totalPages / PAGE_PICKER_SIZE))
const pagePickerStart = computed(() => (pagePickerPage.value - 1) * PAGE_PICKER_SIZE + 1)
const pagePickerEnd = computed(() =>
  Math.min(props.totalPages, pagePickerStart.value + PAGE_PICKER_SIZE - 1),
)
const pagePickerNumbers = computed(() =>
  Array.from(
    { length: Math.max(0, pagePickerEnd.value - pagePickerStart.value + 1) },
    (_, index) => pagePickerStart.value + index,
  ),
)

const pageTokens = computed<PageToken[]>(() => {
  if (props.totalPages <= 5) {
    return Array.from({ length: props.totalPages }, (_, index) => index + 1)
  }

  if (props.page <= 3) {
    return [1, 2, 3, 'ellipsis-end', props.totalPages]
  }

  if (props.page >= props.totalPages - 2) {
    return [1, 'ellipsis-start', props.totalPages - 2, props.totalPages - 1, props.totalPages]
  }

  return [1, 'ellipsis-start', props.page, 'ellipsis-end', props.totalPages]
})

function pickerPageFor(page: number): number {
  if (pagePickerPageCount.value === 0) return 1
  return Math.min(pagePickerPageCount.value, Math.max(1, Math.ceil(page / PAGE_PICKER_SIZE)))
}

function togglePagePicker(token: EllipsisToken): void {
  if (pagePickerOpen.value && activeEllipsis.value === token) {
    pagePickerOpen.value = false
    activeEllipsis.value = null
    return
  }

  pagePickerPage.value = pickerPageFor(props.page)
  activeEllipsis.value = token
  pagePickerOpen.value = true
}

function closePagePicker(): void {
  pagePickerOpen.value = false
  activeEllipsis.value = null
}

function goToPage(page: number): void {
  closePagePicker()
  emit('change', page)
}

function handlePageSizeChange(event: Event): void {
  const value = Number((event.target as HTMLSelectElement).value)
  if (Number.isInteger(value) && value > 0) {
    closePagePicker()
    emit('page-size-change', value)
  }
}

watch(
  () => [props.page, props.totalPages] as const,
  ([page]) => {
    if (!pagePickerOpen.value) {
      pagePickerPage.value = pickerPageFor(page)
    }
  },
  { immediate: true },
)
</script>

<template>
  <nav v-if="totalItems > 0" class="pagination-bar" aria-label="分页">
    <span class="pagination-bar__total">共 {{ totalItems }} 条</span>
    <label class="pagination-bar__size">
      每页
      <select :value="pageSize" aria-label="每页数量" @change="handlePageSizeChange">
        <option v-for="option in pageSizeOptions" :key="option" :value="option">
          {{ option }}
        </option>
      </select>
      条
    </label>
    <div class="pagination-bar__controls">
      <button type="button" :disabled="page <= 1" @click="goToPage(page - 1)">
        上一页
      </button>
      <template v-for="token in pageTokens" :key="token">
        <button
          v-if="typeof token === 'number'"
          type="button"
          class="pagination-bar__page"
          :class="{ 'pagination-bar__page--active': token === page }"
          :aria-current="token === page ? 'page' : undefined"
          @click="goToPage(token)"
        >
          {{ token }}
        </button>
        <span v-else class="pagination-bar__ellipsis-anchor">
          <button
            type="button"
            class="pagination-bar__ellipsis"
            aria-label="打开页码选择器"
            :aria-expanded="pagePickerOpen && activeEllipsis === token"
            @click="togglePagePicker(token)"
          >
            …
          </button>
          <section
            v-if="pagePickerOpen && activeEllipsis === token"
            class="pagination-bar__picker"
            :class="{
              'pagination-bar__picker--start': token === 'ellipsis-start',
              'pagination-bar__picker--end': token === 'ellipsis-end',
            }"
            aria-label="页码选择器"
          >
            <div class="pagination-bar__picker-header">
              <button
                type="button"
                :disabled="pagePickerPage <= 1"
                aria-label="上一组页码"
                @click="pagePickerPage -= 1"
              >
                上一组
              </button>
              <span aria-live="polite">第 {{ pagePickerStart }}-{{ pagePickerEnd }} 页，共 {{ totalPages }} 页</span>
              <button
                type="button"
                :disabled="pagePickerPage >= pagePickerPageCount"
                aria-label="下一组页码"
                @click="pagePickerPage += 1"
              >
                下一组
              </button>
            </div>
            <div class="pagination-bar__picker-grid pagination-bar__picker-grid--five-columns">
              <button
                v-for="pageNumber in pagePickerNumbers"
                :key="pageNumber"
                type="button"
                class="pagination-bar__picker-page"
                :class="{ 'pagination-bar__page--active': pageNumber === page }"
                :aria-current="pageNumber === page ? 'page' : undefined"
                @click="goToPage(pageNumber)"
              >
                {{ pageNumber }}
              </button>
            </div>
          </section>
        </span>
      </template>
      <button type="button" :disabled="page >= totalPages || totalPages === 0" @click="goToPage(page + 1)">
        下一页
      </button>
    </div>
  </nav>
</template>

<style scoped>
.pagination-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  color: var(--color-text-secondary);
}

.pagination-bar__size {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.pagination-bar select {
  min-width: 4.5rem;
  padding: var(--space-1) var(--space-2);
}

.pagination-bar__controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-1);
}

.pagination-bar button {
  min-width: 2.25rem;
  padding: var(--space-1) var(--space-2);
}

.pagination-bar__ellipsis {
  border-color: transparent;
  background: transparent;
  color: var(--color-text-secondary);
}

.pagination-bar__ellipsis-anchor {
  position: relative;
  display: inline-flex;
}

.pagination-bar__picker {
  position: absolute;
  top: calc(100% + var(--space-2));
  z-index: 20;
  display: grid;
  gap: var(--space-3);
  width: min(24rem, calc(100vw - 2rem));
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-md);
}

.pagination-bar__picker--start {
  left: 0;
}

.pagination-bar__picker--end {
  right: 0;
}

.pagination-bar__picker::before {
  content: '';
  position: absolute;
  top: -0.4rem;
  width: 0.75rem;
  height: 0.75rem;
  border-top: 1px solid var(--color-border);
  border-left: 1px solid var(--color-border);
  background: var(--color-surface-raised);
  transform: rotate(45deg);
}

.pagination-bar__picker--start::before {
  left: 1rem;
}

.pagination-bar__picker--end::before {
  right: 1rem;
}

.pagination-bar__picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.pagination-bar__picker-grid {
  display: grid;
  gap: var(--space-1);
  max-width: 30rem;
}

.pagination-bar__picker-grid--five-columns {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.pagination-bar__picker-page {
  width: 100%;
}

.pagination-bar__page--active {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: var(--color-on-primary);
}

@media (max-width: 40rem) {
  .pagination-bar {
    align-items: stretch;
    flex-direction: column;
  }

  .pagination-bar__controls {
    justify-content: center;
  }

  .pagination-bar__picker-header {
    align-items: stretch;
    flex-direction: column;
    text-align: center;
  }

  .pagination-bar__picker-grid {
    width: 100%;
  }
}
</style>
