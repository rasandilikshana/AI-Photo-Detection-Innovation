<script setup lang="ts">
import { computed } from 'vue'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Shield, MapPin, Clock, Smartphone } from 'lucide-vue-next'

interface Props {
  riskScore: number
  riskLevel: string
  riskFactors?: string[]
  uniqueIpCount?: number
  uniqueSessionCount?: number
  uniqueUserAgentCount?: number
  timeGapAnomalies?: any[]
  geoAnomalies?: any[]
  investigationStatus?: string
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  riskFactors: () => [],
  compact: false
})

const alertVariant = computed(() => {
  switch (props.riskLevel) {
    case 'high':
      return 'destructive'
    case 'medium':
      return 'default'
    case 'low':
      return 'default'
    default:
      return 'default'
  }
})

const riskColor = computed(() => {
  switch (props.riskLevel) {
    case 'high':
      return 'text-destructive'
    case 'medium':
      return 'text-warning'
    case 'low':
      return 'text-success'
    default:
      return 'text-muted-foreground'
  }
})

const statusColor = computed(() => {
  switch (props.investigationStatus) {
    case 'pending':
      return 'bg-warning/10 text-warning'
    case 'reviewing':
      return 'bg-info/10 text-info'
    case 'resolved':
      return 'bg-success/10 text-success'
    case 'no_action_needed':
      return 'bg-secondary text-muted-foreground'
    default:
      return 'bg-secondary text-muted-foreground'
  }
})

const showAlert = computed(() => {
  return props.riskLevel === 'high' || props.riskLevel === 'medium'
})
</script>

<template>
  <Alert v-if="showAlert" :variant="alertVariant">
    <AlertTriangle class="h-4 w-4" />
    <AlertTitle class="flex items-center gap-2">
      <span>{{ riskLevel === 'high' ? 'High' : 'Medium' }} Security Risk Detected</span>
      <Badge
        v-if="investigationStatus"
        :class="statusColor"
        class="capitalize text-xs"
      >
        {{ investigationStatus.replace('_', ' ') }}
      </Badge>
    </AlertTitle>
    <AlertDescription>
      <div class="space-y-3 mt-2">
        <!-- Risk Score -->
        <div class="flex items-center justify-between">
          <span class="text-sm">Risk Score</span>
          <span :class="['text-sm font-bold', riskColor]">
            {{ (riskScore * 100).toFixed(0) }}%
          </span>
        </div>

        <!-- Activity Indicators (Compact View) -->
        <div v-if="compact" class="flex flex-wrap gap-2 text-xs">
          <div v-if="uniqueIpCount" class="flex items-center gap-1">
            <MapPin class="h-3 w-3" />
            <span>{{ uniqueIpCount }} IPs</span>
          </div>
          <div v-if="uniqueSessionCount" class="flex items-center gap-1">
            <Shield class="h-3 w-3" />
            <span>{{ uniqueSessionCount }} sessions</span>
          </div>
          <div v-if="uniqueUserAgentCount" class="flex items-center gap-1">
            <Smartphone class="h-3 w-3" />
            <span>{{ uniqueUserAgentCount }} devices</span>
          </div>
        </div>

        <!-- Risk Factors -->
        <div v-if="riskFactors && riskFactors.length > 0" class="space-y-1">
          <p class="text-sm font-semibold">Detected Issues:</p>
          <ul class="text-sm space-y-1 ml-4 list-disc">
            <li v-for="(factor, index) in riskFactors" :key="index">
              {{ factor }}
            </li>
          </ul>
        </div>

        <!-- Detailed Metrics (Full View) -->
        <div v-if="!compact" class="grid grid-cols-3 gap-3 mt-3">
          <div v-if="uniqueIpCount" class="space-y-1">
            <div class="flex items-center gap-1 text-xs text-muted-foreground">
              <MapPin class="h-3 w-3" />
              <span>IP Addresses</span>
            </div>
            <p class="text-lg font-display font-semibold">{{ uniqueIpCount }}</p>
            <p class="text-xs text-muted-foreground">
              {{ uniqueIpCount > 3 ? 'Suspicious' : 'Normal' }}
            </p>
          </div>

          <div v-if="uniqueSessionCount" class="space-y-1">
            <div class="flex items-center gap-1 text-xs text-muted-foreground">
              <Shield class="h-3 w-3" />
              <span>Sessions</span>
            </div>
            <p class="text-lg font-display font-semibold">{{ uniqueSessionCount }}</p>
            <p class="text-xs text-muted-foreground">Active sessions</p>
          </div>

          <div v-if="uniqueUserAgentCount" class="space-y-1">
            <div class="flex items-center gap-1 text-xs text-muted-foreground">
              <Smartphone class="h-3 w-3" />
              <span>Devices</span>
            </div>
            <p class="text-lg font-display font-semibold">{{ uniqueUserAgentCount }}</p>
            <p class="text-xs text-muted-foreground">
              {{ uniqueUserAgentCount > 3 ? 'Multiple' : 'Few' }} devices
            </p>
          </div>
        </div>

        <!-- Time Gap Anomalies -->
        <div v-if="!compact && timeGapAnomalies && timeGapAnomalies.length > 0" class="space-y-1">
          <p class="text-sm font-semibold flex items-center gap-1">
            <Clock class="h-3 w-3" />
            Impossible Time Gaps ({{ timeGapAnomalies.length }})
          </p>
          <p class="text-xs text-muted-foreground">
            Activity detected from different locations with insufficient travel time
          </p>
        </div>

        <!-- Geographic Anomalies -->
        <div v-if="!compact && geoAnomalies && geoAnomalies.length > 0" class="space-y-1">
          <p class="text-sm font-semibold flex items-center gap-1">
            <MapPin class="h-3 w-3" />
            Geographic Inconsistencies ({{ geoAnomalies.length }})
          </p>
          <p class="text-xs text-muted-foreground">
            Activities from multiple network blocks detected
          </p>
        </div>

        <!-- Recommendation -->
        <div v-if="riskLevel === 'high'" class="mt-3 pt-3 border-t">
          <p class="text-sm font-semibold">Recommendation:</p>
          <p class="text-sm">
            Immediate admin review recommended. Consider temporarily suspending account access
            pending investigation.
          </p>
        </div>
        <div v-else-if="riskLevel === 'medium'" class="mt-3 pt-3 border-t">
          <p class="text-sm font-semibold">Recommendation:</p>
          <p class="text-sm">
            Continue monitoring activity patterns. Contact judge if anomalies persist.
          </p>
        </div>
      </div>
    </AlertDescription>
  </Alert>
</template>
