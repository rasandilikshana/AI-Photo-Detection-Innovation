<template>
  <div class="loading-spinner" :class="{ 'full-page': fullPage }">
    <v-progress-circular
      :size="size"
      :width="width"
      :color="color"
      indeterminate
    />
    <p v-if="message" class="text-center mt-4 text-medium-emphasis">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  size?: number
  width?: number
  color?: string
  message?: string
  fullPage?: boolean
}

withDefaults(defineProps<Props>(), {
  size: 64,
  width: 4,
  color: 'primary',
  message: '',
  fullPage: false,
})
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.loading-spinner.full-page {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(255, 255, 255, 0.9);
  z-index: 9999;
}
</style>
