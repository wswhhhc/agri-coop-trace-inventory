<script setup lang="ts">
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
</script>

<template>
  <section class="forbidden-page">
    <PageHeader title="403 无权限" description="当前账号没有访问此页面的权限。" />
    <PageContext />
    <p class="forbidden-page__placeholder">请从左侧菜单选择当前账号被授权的功能。</p>
  </section>
</template>
