<script setup lang="ts">
import { useRoute } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
</script>

<template>
  <dl class="page-context">
    <div class="page-context__item">
      <dt>当前路径</dt>
      <dd>{{ route.fullPath }}</dd>
    </div>
    <div class="page-context__item">
      <dt>当前用户</dt>
      <dd>{{ authStore.user?.displayName }}</dd>
    </div>
    <div class="page-context__item">
      <dt>当前角色</dt>
      <dd>{{ authStore.role }}</dd>
    </div>
  </dl>
</template>

<style scoped>
.page-context {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-6);
}

.page-context__item {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  padding: var(--space-1) var(--space-3);
  background: var(--color-surface-muted);
  font-size: var(--font-size-xs);
}

.page-context__item dt {
  color: var(--color-text-muted);
}

.page-context__item dd {
  overflow: hidden;
  max-width: 18rem;
  margin: 0;
  color: var(--color-text-secondary);
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 48rem) {
  .page-context__item dd {
    max-width: 12rem;
  }
}
</style>
