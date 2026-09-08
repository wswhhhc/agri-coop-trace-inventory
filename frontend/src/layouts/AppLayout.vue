<script setup lang="ts">
import { ref } from 'vue'

import PageContainer from '@/components/common/PageContainer.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'

const sidebarOpen = ref(false)

function toggleSidebar(): void {
  sidebarOpen.value = !sidebarOpen.value
}

function closeSidebar(): void {
  sidebarOpen.value = false
}
</script>

<template>
  <div class="app-layout">
    <AppSidebar :open="sidebarOpen" @close="closeSidebar" />
    <div class="app-layout__main">
      <AppHeader @toggle-sidebar="toggleSidebar" />
      <PageContainer>
        <RouterView />
      </PageContainer>
    </div>
    <button
      v-if="sidebarOpen"
      class="app-layout__scrim"
      type="button"
      aria-label="关闭导航"
      @click="closeSidebar"
    />
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100dvh;
  background: var(--color-bg);
}

.app-layout__main {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
}

.app-layout__scrim {
  display: none;
}

@media (max-width: 48rem) {
  .app-layout__scrim {
    position: fixed;
    z-index: 15;
    display: block;
    inset: 0;
    width: 100%;
    min-height: 100%;
    border: 0;
    border-radius: 0;
    padding: 0;
    background: var(--color-overlay);
  }
}
</style>
