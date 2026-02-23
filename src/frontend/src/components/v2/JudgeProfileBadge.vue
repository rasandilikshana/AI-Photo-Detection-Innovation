<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'
import { TrendingDown, TrendingUp, CheckCircle, AlertTriangle } from 'lucide-vue-next'

interface Props {
  biasScore?: number
  biasCategory?: string
  consistencyScore?: number
  submissionCount?: number
  size?: 'sm' | 'md' | 'lg'
  showDetails?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  biasScore: 0,
  biasCategory: 'neutral',
  consistencyScore: 0,
  submissionCount: 0,
  size: 'md',
  showDetails: false
})

const badgeVariant = computed(() => {
  switch (props.biasCategory) {
    case 'neutral':
      return 'default'
    case 'harsh':
    case 'lenient':
      return 'secondary'
    default:
      return 'outline'
  }
})

const badgeColor = computed(() => {
  switch (props.biasCategory) {
    case 'harsh':
      return 'bg-red-500/10 text-red-600 dark:text-red-400'
    case 'lenient':
      return 'bg-green-500/10 text-green-600 dark:text-green-400'
    case 'neutral':
      return 'bg-blue-500/10 text-blue-600 dark:text-blue-400'
    default:
      return 'bg-gray-500/10 text-gray-600 dark:text-gray-400'
  }
})

const icon = computed(() => {
  switch (props.biasCategory) {
    case 'harsh':
      return TrendingDown
    case 'lenient':
      return TrendingUp
    case 'neutral':
      return CheckCircle
    default:
      return AlertTriangle
  }
})

const biasLabel = computed(() => {
  const absScore = Math.abs(props.biasScore)
  if (absScore > 2.0) return 'Significant'
  if (absScore > 1.0) return 'Moderate'
  return props.biasCategory
})

const consistencyLevel = computed(() => {
  if (props.consistencyScore >= 0.8) return 'Excellent'
  if (props.consistencyScore >= 0.6) return 'Good'
  if (props.consistencyScore >= 0.4) return 'Fair'
  return 'Poor'
})

const consistencyColor = computed(() => {
  if (props.consistencyScore >= 0.8) return 'text-green-600 dark:text-green-400'
  if (props.consistencyScore >= 0.6) return 'text-blue-600 dark:text-blue-400'
  if (props.consistencyScore >= 0.4) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
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
    <!-- Bias Badge -->
    <div class="flex items-center gap-2 flex-wrap">
      <Badge :variant="badgeVariant" :class="[badgeColor, sizeClasses]">
        <component :is="icon" class="h-3 w-3 mr-1" />
        <span class="capitalize">{{ biasLabel }}</span>
      </Badge>

      <!-- Bias Score -->
      <span v-if="biasScore !== 0" :class="['font-medium', sizeClasses]">
        {{ biasScore > 0 ? '+' : '' }}{{ biasScore.toFixed(2) }}
      </span>
    </div>

    <!-- Details -->
    <div v-if="showDetails" class="flex flex-col gap-1 text-xs text-muted-foreground">
      <!-- Consistency -->
      <div v-if="consistencyScore > 0" class="flex items-center justify-between">
        <span>Consistency:</span>
        <span :class="['font-medium', consistencyColor]">
          {{ (consistencyScore * 100).toFixed(0) }}% ({{ consistencyLevel }})
        </span>
      </div>

      <!-- Submissions Scored -->
      <div v-if="submissionCount > 0" class="flex items-center justify-between">
        <span>Scored:</span>
        <span class="font-medium">{{ submissionCount }} submissions</span>
      </div>

      <!-- Bias Explanation -->
      <p v-if="Math.abs(biasScore) > 2.0" class="text-amber-600 dark:text-amber-400 mt-1">
        <AlertTriangle class="h-3 w-3 inline mr-1" />
        Z-score > 2.0: Significant bias detected
      </p>
    </div>
  </div>
</template>
