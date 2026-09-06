<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()

const breadcrumbItems = computed(() =>
  route.matched
    .filter((record) => record.meta.title)
    .map((record) => ({
      title: record.meta.title as string,
      path: record.path,
    })),
)
</script>

<template>
  <nav class="app-breadcrumb" aria-label="面包屑">
    <ol class="app-breadcrumb__list">
      <li v-for="(item, index) in breadcrumbItems" :key="item.path" class="app-breadcrumb__item">
        <RouterLink v-if="index < breadcrumbItems.length - 1" :to="item.path">
          {{ item.title }}
        </RouterLink>
        <span v-else aria-current="page">{{ item.title }}</span>
      </li>
    </ol>
  </nav>
</template>

<style scoped>
.app-breadcrumb {
  padding: var(--space-5) var(--space-8) 0;
}

.app-breadcrumb__list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin: 0;
  padding: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  list-style: none;
}

.app-breadcrumb__item:not(:last-child)::after {
  margin-left: var(--space-2);
  color: var(--color-text-muted);
  content: '/';
}

@media (max-width: 64rem) {
  .app-breadcrumb {
    padding-inline: var(--space-5);
  }
}

@media (max-width: 48rem) {
  .app-breadcrumb {
    padding: var(--space-4) var(--space-4) 0;
  }
}
</style>
