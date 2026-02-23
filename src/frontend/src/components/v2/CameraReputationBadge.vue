<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Camera, Shield, AlertTriangle, CheckCircle } from 'lucide-vue-next'

interface Props {
  trustScore?: number
  boost?: number
  cameraMake?: string
  cameraModel?: string
  verified?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  trustScore: 0,
  boost: 0,
  size: 'md'
})

const trustLevel = computed(() => {
  if (!props.trustScore) return 'unknown'
  if (props.trustScore >= 0.8) return 'high'
  if (props.trustScore >= 0.6) return 'medium'
  if (props.trustScore >= 0.4) return 'low'
  return 'suspicious'
})

const badgeVariant = computed(() => {
  switch (trustLevel.value) {
    case 'high':
      return 'default'
    case 'medium':
      return 'secondary'
    case 'low':
      return 'outline'
    case 'suspicious':
      return 'destructive'
    default:
      return 'outline'
  }
})

const badgeColor = computed(() => {
  switch (trustLevel.value) {
    case 'high':
      return 'text-green-600 dark:text-green-400'
    case 'medium':
      return 'text-blue-600 dark:text-blue-400'
    case 'low':
      return 'text-yellow-600 dark:text-yellow-400'
    case 'suspicious':
      return 'text-red-600 dark:text-red-400'
    default:
      return 'text-gray-600 dark:text-gray-400'
  }
})

const icon = computed(() => {
  if (!props.verified) return AlertTriangle
  switch (trustLevel.value) {
    case 'high':
    case 'medium':
      return CheckCircle
    case 'low':
    case 'suspicious':
      return Shield
    default:
      return Camera
  }
})

const boostText = computed(() => {
  if (props.boost === 0) return 'No boost'
  const sign = props.boost > 0 ? '+' : ''
  return `${sign}${(props.boost * 100).toFixed(0)}%`
})

const boostColor = computed(() => {
  if (props.boost > 0.1) return 'text-green-600 dark:text-green-400'
  if (props.boost > 0) return 'text-blue-600 dark:text-blue-400'
  if (props.boost < 0) return 'text-red-600 dark:text-red-400'
  return 'text-gray-600 dark:text-gray-400'
})

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'text-xs'
    case 'lg':
      return 'text-base'
    default:
      return 'text-sm'
  }
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <!-- Camera Info -->
    <div v-if="cameraMake && cameraModel" class="flex items-center gap-2 text-sm text-muted-foreground">
      <Camera class="h-4 w-4" />
      <span>{{ cameraMake }} {{ cameraModel }}</span>
    </div>

    <!-- Trust Badge -->
    <div class="flex items-center gap-2">
      <Badge :variant="badgeVariant" :class="sizeClasses">
        <component :is="icon" class="h-3 w-3 mr-1" />
        <span class="capitalize">{{ trustLevel }} Trust</span>
      </Badge>

      <!-- Trust Score -->
      <span v-if="trustScore > 0" :class="['font-medium', badgeColor, sizeClasses]">
        {{ (trustScore * 100).toFixed(0) }}%
      </span>

      <!-- Boost Indicator -->
      <Badge v-if="boost !== 0" variant="outline" :class="[sizeClasses, boostColor]">
        {{ boostText }}
      </Badge>
    </div>

    <!-- Verified Indicator -->
    <div v-if="verified === false" class="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
      <AlertTriangle class="h-3 w-3" />
      <span>PRNU verification pending</span>
    </div>
  </div>
</template>
