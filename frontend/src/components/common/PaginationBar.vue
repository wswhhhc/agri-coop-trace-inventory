<script setup lang="ts">
import { computed } from 'vue'

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

const pageNumbers = computed(() =>
  Array.from({ length: props.totalPages }, (_, index) => index + 1),
)

function handlePageSizeChange(event: Event): void {
  const value = Number((event.target as HTMLSelectElement).value)
  if (Number.isInteger(value) && value > 0) {
    emit('page-size-change', value)
  }
}
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
      <button type="button" :disabled="page <= 1" @click="emit('change', page - 1)">
        上一页
      </button>
      <button
        v-for="pageNumber in pageNumbers"
        :key="pageNumber"
        type="button"
        :class="{ 'pagination-bar__page--active': pageNumber === page }"
        :aria-current="pageNumber === page ? 'page' : undefined"
        @click="emit('change', pageNumber)"
      >
        {{ pageNumber }}
      </button>
      <button type="button" :disabled="page >= totalPages || totalPages === 0" @click="emit('change', page + 1)">
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
  gap: var(--space-1);
}

.pagination-bar button {
  min-width: 2.25rem;
  padding: var(--space-1) var(--space-2);
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
}
</style>
