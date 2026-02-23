<template>
  <div class="relative h-2 w-full overflow-hidden rounded-full bg-secondary">
    <div
      class="h-full bg-primary transition-all"
      :style="{ width: `${Math.min(100, Math.max(0, modelValue))}%` }"
    />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: number
}>()
</script>
