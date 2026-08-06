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
  boost: 0,
  size: 'md'
})

const trustLevel = computed(() => {
  // Distinguish between undefined (no data) and 0 (initial state)
  if (props.trustScore === undefined || props.trustScore === null) return 'pending'
  if (props.trustScore === 0) return 'initial'
  if (props.trustScore >= 0.8) return 'high'
  if (props.trustScore >= 0.6) return 'medium'
  if (props.trustScore >= 0.4) return 'low'
  return 'suspicious'
})

const trustLabel = computed(() => {
  switch (trustLevel.value) {
    case 'high': return 'High Trust'
    case 'medium': return 'Medium Trust'
    case 'low': return 'Low Trust'
    case 'suspicious': return 'Suspicious'
    case 'initial': return 'Building Trust'
    case 'pending': return 'Analyzing'
    default: return 'Unknown'
  }
})

const badgeVariant = computed(() => {
  switch (trustLevel.value) {
    case 'high':
      return 'default'
    case 'medium':
      return 'secondary'
    case 'low':
    case 'initial':
      return 'outline'
    case 'suspicious':
      return 'destructive'
    case 'pending':
      return 'secondary'
    default:
      return 'outline'
  }
})

const badgeColor = computed(() => {
  switch (trustLevel.value) {
    case 'high':
      return 'text-success'
    case 'medium':
      return 'text-info'
    case 'low':
      return 'text-warning'
    case 'initial':
      return 'text-info'
    case 'suspicious':
      return 'text-destructive'
    case 'pending':
      return 'text-muted-foreground'
    default:
      return 'text-muted-foreground'
  }
})

const icon = computed(() => {
  if (!props.verified && trustLevel.value !== 'pending') return AlertTriangle
  switch (trustLevel.value) {
    case 'high':
    case 'medium':
      return CheckCircle
    case 'low':
    case 'suspicious':
      return Shield
    case 'initial':
    case 'pending':
      return Camera
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
  if (props.boost > 0.1) return 'text-success'
  if (props.boost > 0) return 'text-info'
  if (props.boost < 0) return 'text-destructive'
  return 'text-muted-foreground'
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

// Compute display name avoiding duplicates like "Canon Canon EOS 600D"
const cameraDisplayName = computed(() => {
  const make = props.cameraMake?.trim() || ''
  const model = props.cameraModel?.trim() || ''

  if (!make && !model) return ''
  if (!make) return model
  if (!model) return make

  // If model already starts with make, just show model
  if (model.toLowerCase().startsWith(make.toLowerCase())) {
    return model
  }

  return `${make} ${model}`
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <!-- Camera Info -->
    <div v-if="cameraDisplayName" class="flex items-center gap-2 text-sm text-muted-foreground">
      <Camera class="h-4 w-4" />
      <span>{{ cameraDisplayName }}</span>
    </div>

    <!-- Trust Badge -->
    <div class="flex items-center gap-2">
      <Badge :variant="badgeVariant" :class="sizeClasses">
        <component :is="icon" class="h-3 w-3 mr-1" />
        <span>{{ trustLabel }}</span>
      </Badge>

      <!-- Trust Score -->
      <span v-if="trustScore !== undefined && trustScore !== null && trustScore > 0" :class="['font-medium', badgeColor, sizeClasses]">
        {{ (trustScore * 100).toFixed(0) }}%
      </span>

      <!-- Boost Indicator -->
      <Badge v-if="boost !== 0" variant="outline" :class="[sizeClasses, boostColor]">
        {{ boostText }}
      </Badge>
    </div>

    <!-- Verified Indicator -->
    <div v-if="verified === false && trustLevel !== 'pending'" class="flex items-center gap-1 text-xs text-warning">
      <AlertTriangle class="h-3 w-3" />
      <span>PRNU verification pending</span>
    </div>
    <div v-else-if="trustLevel === 'initial'" class="flex items-center gap-1 text-xs text-info">
      <Camera class="h-3 w-3" />
      <span>First submission from this camera - building trust profile</span>
    </div>
  </div>
</template>
