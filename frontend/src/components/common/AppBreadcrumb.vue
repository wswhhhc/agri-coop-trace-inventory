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
