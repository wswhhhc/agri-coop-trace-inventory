<template>
  <main class="page-container">
    <slot />
  </main>
</template>

<style scoped>
.page-container {
  width: min(100%, 96rem);
  margin: 0 auto;
  padding: var(--space-6) var(--space-8) var(--space-12);
}

@media (max-width: 64rem) {
  .page-container {
    padding-inline: var(--space-5);
  }
}

@media (max-width: 48rem) {
  .page-container {
    padding: var(--space-5) var(--space-4) var(--space-10);
  }
}
</style>
