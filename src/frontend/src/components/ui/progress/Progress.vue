<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  modelValue: number
  class?: HTMLAttributes['class']
  label?: string
}>()
</script>

<template>
  <div
    role="progressbar"
    :aria-valuenow="Math.round(Math.min(100, Math.max(0, props.modelValue)))"
    aria-valuemin="0"
    aria-valuemax="100"
    :aria-label="props.label"
    :class="cn('relative h-2 w-full overflow-hidden rounded-full bg-secondary', props.class)"
  >
    <div
      class="h-full bg-primary transition-all"
      :style="{ width: `${Math.min(100, Math.max(0, props.modelValue))}%` }"
    />
  </div>
</template>
