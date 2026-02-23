<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Users, CheckCircle, AlertCircle, AlertTriangle, XCircle } from 'lucide-vue-next'

interface Props {
  icc?: number
  verdict?: string
  judgeCount?: number
  outlierCount?: number
  flaggedForReview?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  icc: 0,
  verdict: 'insufficient_data',
  judgeCount: 0,
  outlierCount: 0,
  flaggedForReview: false,
  size: 'md'
})

const verdictLabel = computed(() => {
  switch (props.verdict) {
    case 'strong_consensus':
      return 'Strong Consensus'
    case 'moderate_consensus':
      return 'Moderate Consensus'
    case 'weak_consensus':
      return 'Weak Consensus'
    case 'poor_consensus':
      return 'Poor Consensus'
    case 'insufficient_data':
      return 'Insufficient Data'
    default:
      return props.verdict
  }
})

const verdictColor = computed(() => {
  switch (props.verdict) {
    case 'strong_consensus':
      return 'text-green-600 dark:text-green-400'
    case 'moderate_consensus':
      return 'text-blue-600 dark:text-blue-400'
    case 'weak_consensus':
      return 'text-yellow-600 dark:text-yellow-400'
    case 'poor_consensus':
      return 'text-red-600 dark:text-red-400'
    default:
      return 'text-gray-600 dark:text-gray-400'
  }
})

const badgeVariant = computed(() => {
  switch (props.verdict) {
    case 'strong_consensus':
      return 'default'
    case 'moderate_consensus':
      return 'secondary'
    case 'weak_consensus':
      return 'outline'
    case 'poor_consensus':
      return 'destructive'
    default:
      return 'outline'
  }
})

const icon = computed(() => {
  switch (props.verdict) {
    case 'strong_consensus':
      return CheckCircle
    case 'moderate_consensus':
      return CheckCircle
    case 'weak_consensus':
      return AlertCircle
    case 'poor_consensus':
      return XCircle
    default:
      return AlertTriangle
  }
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
    <!-- Consensus Badge -->
    <div class="flex items-center gap-2 flex-wrap">
      <Badge :variant="badgeVariant" :class="sizeClasses">
        <component :is="icon" class="h-3 w-3 mr-1" />
        {{ verdictLabel }}
      </Badge>

      <!-- ICC Score -->
      <span v-if="icc > 0" :class="['font-medium', verdictColor, sizeClasses]">
        ICC: {{ icc.toFixed(2) }}
      </span>

      <!-- Judge Count -->
      <div v-if="judgeCount > 0" class="flex items-center gap-1 text-muted-foreground" :class="sizeClasses">
        <Users class="h-3 w-3" />
        <span>{{ judgeCount }} judges</span>
      </div>
    </div>

    <!-- Warning Indicators -->
    <div class="flex flex-col gap-1">
      <!-- Flagged for Review -->
      <div v-if="flaggedForReview" class="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
        <AlertTriangle class="h-3 w-3" />
        <span>Flagged for manual review</span>
      </div>

      <!-- Outlier Judges -->
      <div v-if="outlierCount > 0" class="flex items-center gap-1 text-xs text-red-600 dark:text-red-400">
        <AlertCircle class="h-3 w-3" />
        <span>{{ outlierCount }} outlier judge{{ outlierCount > 1 ? 's' : '' }} detected</span>
      </div>
    </div>
  </div>
</template>
