<script setup lang="ts">
import AppBreadcrumb from '@/components/common/AppBreadcrumb.vue'
import PageContainer from '@/components/common/PageContainer.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
</script>

<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="app-layout__main">
      <AppHeader />
      <AppBreadcrumb />
      <PageContainer>
        <RouterView />
      </PageContainer>
    </div>
  </div>
</template>
