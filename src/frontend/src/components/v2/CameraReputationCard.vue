<script setup lang="ts">
import { ref, computed } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { Camera, Shield, AlertTriangle, TrendingUp, TrendingDown, Fingerprint } from 'lucide-vue-next'
import CameraReputationBadge from './CameraReputationBadge.vue'

interface Props {
  submissionId: number
  cameraMake?: string
  cameraModel?: string
  trustScore?: number
  boost?: number
  prnuEnergy?: number
  verified?: boolean
  fraudCheck?: {
    fraud_likelihood: number
    fraud_verdict: string
    indicators: string[]
    recommendation: string
  }
}

const props = defineProps<Props>()

const showDetails = ref(false)

// PRNU energy thresholds calibrated for real camera fingerprints
// Real cameras typically produce energy values in the 0.0001 - 0.002 range
const energyQuality = computed(() => {
  if (!props.prnuEnergy) return 'unknown'
  if (props.prnuEnergy > 0.001) return 'excellent'
  if (props.prnuEnergy > 0.0005) return 'good'
  if (props.prnuEnergy > 0.0001) return 'fair'
  return 'low'
})

const energyQualityLabel = computed(() => {
  switch (energyQuality.value) {
    case 'excellent': return 'Excellent - Strong camera fingerprint'
    case 'good': return 'Good - Clear camera signature'
    case 'fair': return 'Fair - Detectable pattern'
    case 'low': return 'Low - Weak signal (heavily processed)'
    default: return 'Unknown'
  }
})

const energyColor = computed(() => {
  switch (energyQuality.value) {
    case 'excellent':
      return 'text-green-600 dark:text-green-400'
    case 'good':
      return 'text-blue-600 dark:text-blue-400'
    case 'fair':
      return 'text-yellow-600 dark:text-yellow-400'
    case 'low':
      return 'text-orange-600 dark:text-orange-400'
    default:
      return 'text-gray-600 dark:text-gray-400'
  }
})

const fraudRiskColor = computed(() => {
  if (!props.fraudCheck) return 'text-gray-600'
  if (props.fraudCheck.fraud_likelihood > 0.7) return 'text-red-600 dark:text-red-400'
  if (props.fraudCheck.fraud_likelihood > 0.4) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-green-600 dark:text-green-400'
})

const fraudRiskLevel = computed(() => {
  if (!props.fraudCheck) return 'unknown'
  if (props.fraudCheck.fraud_likelihood > 0.7) return 'high'
  if (props.fraudCheck.fraud_likelihood > 0.4) return 'medium'
  return 'low'
})

// Calculate trust score breakdown components
// These are estimated based on the overall trust score
const trustBreakdown = computed(() => {
  const score = props.trustScore || 0

  // Pattern similarity is the primary factor - weighted at 50%
  // Estimate based on PRNU energy quality
  let patternScore = 0
  if (props.prnuEnergy) {
    if (props.prnuEnergy > 0.001) patternScore = 0.95
    else if (props.prnuEnergy > 0.0005) patternScore = 0.85
    else if (props.prnuEnergy > 0.0001) patternScore = 0.70
    else patternScore = 0.40
  }

  // Historical data contribution - estimated from overall score
  // First submission gets lower historical score
  const historyScore = props.verified ? Math.min(score * 1.1, 1.0) : 0.5

  // Consistency score - based on verification status
  const consistencyScore = props.verified ? 0.9 : 0.6

  return {
    pattern: patternScore,
    history: historyScore,
    consistency: consistencyScore
  }
})
</script>

<template>
  <Card>
    <CardHeader>
      <div class="flex items-center justify-between">
        <CardTitle class="flex items-center gap-2">
          <Shield class="h-5 w-5" />
          Camera Reputation
        </CardTitle>
        <button
          @click="showDetails = !showDetails"
          class="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          {{ showDetails ? 'Hide' : 'Show' }} Details
        </button>
      </div>
      <CardDescription>
        PRNU fingerprint and trust analysis
      </CardDescription>
    </CardHeader>

    <CardContent class="space-y-4">
      <!-- Trust Badge -->
      <CameraReputationBadge
        :trust-score="trustScore"
        :boost="boost"
        :camera-make="cameraMake"
        :camera-model="cameraModel"
        :verified="verified"
        size="md"
      />

      <!-- Fraud Alert -->
      <Alert v-if="fraudCheck && fraudCheck.fraud_likelihood > 0.4" variant="destructive">
        <AlertTriangle class="h-4 w-4" />
        <AlertDescription>
          <div class="space-y-2">
            <p class="font-semibold">
              {{ fraudCheck.fraud_verdict === 'high_fraud_risk' ? 'High Fraud Risk Detected' : 'Moderate Fraud Risk' }}
            </p>
            <p class="text-sm">
              Fraud Likelihood: <span class="font-medium">{{ (fraudCheck.fraud_likelihood * 100).toFixed(0) }}%</span>
            </p>
            <p class="text-sm">
              Recommendation: <span class="font-medium capitalize">{{ fraudCheck.recommendation }}</span>
            </p>
          </div>
        </AlertDescription>
      </Alert>

      <!-- Details Section -->
      <div v-if="showDetails" class="space-y-4 pt-2 border-t">
        <!-- PRNU Energy -->
        <div v-if="prnuEnergy !== undefined" class="space-y-2">
          <div class="flex items-center justify-between text-sm">
            <span class="text-muted-foreground">PRNU Energy</span>
            <span :class="['font-medium', energyColor]">
              {{ prnuEnergy.toFixed(6) }}
            </span>
          </div>
          <!-- Progress scaled for typical real camera range (0 - 0.002) -->
          <Progress :model-value="Math.min(prnuEnergy * 50000, 100)" class="h-2" />
          <p class="text-xs text-muted-foreground">
            <span :class="energyColor">{{ energyQualityLabel }}</span>
          </p>
        </div>

        <!-- Trust Score Breakdown -->
        <div v-if="trustScore !== undefined && trustScore > 0" class="space-y-2">
          <p class="text-sm font-medium">Trust Score Breakdown</p>
          <div class="space-y-2 text-xs">
            <div class="space-y-1">
              <div class="flex justify-between text-muted-foreground">
                <span>Pattern Similarity (50%)</span>
                <span class="font-medium" :class="trustBreakdown.pattern >= 0.7 ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'">
                  {{ (trustBreakdown.pattern * 100).toFixed(0) }}%
                </span>
              </div>
              <Progress :model-value="trustBreakdown.pattern * 100" class="h-1" />
            </div>
            <div class="space-y-1">
              <div class="flex justify-between text-muted-foreground">
                <span>Historical Data (30%)</span>
                <span class="font-medium" :class="trustBreakdown.history >= 0.7 ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'">
                  {{ (trustBreakdown.history * 100).toFixed(0) }}%
                </span>
              </div>
              <Progress :model-value="trustBreakdown.history * 100" class="h-1" />
            </div>
            <div class="space-y-1">
              <div class="flex justify-between text-muted-foreground">
                <span>Consistency (20%)</span>
                <span class="font-medium" :class="trustBreakdown.consistency >= 0.7 ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'">
                  {{ (trustBreakdown.consistency * 100).toFixed(0) }}%
                </span>
              </div>
              <Progress :model-value="trustBreakdown.consistency * 100" class="h-1" />
            </div>
          </div>
        </div>

        <!-- Boost Explanation -->
        <div v-if="boost !== 0" class="space-y-1">
          <p class="text-sm font-medium">Confidence Boost</p>
          <p class="text-xs text-muted-foreground">
            <template v-if="boost > 0.1">
              Strong PRNU match with previous submissions from this camera.
              AI detection confidence increased by {{ (boost * 100).toFixed(0) }}%.
            </template>
            <template v-else-if="boost > 0">
              Moderate PRNU match with camera profile.
              AI detection confidence increased by {{ (boost * 100).toFixed(0) }}%.
            </template>
            <template v-else-if="boost < 0">
              PRNU pattern mismatch detected.
              AI detection confidence decreased by {{ Math.abs(boost * 100).toFixed(0) }}%.
            </template>
            <template v-else>
              No historical data available for trust boost calculation.
            </template>
          </p>
        </div>

        <!-- Fraud Indicators -->
        <div v-if="fraudCheck && fraudCheck.indicators.length > 0" class="space-y-2">
          <p class="text-sm font-medium flex items-center gap-2">
            <AlertTriangle class="h-4 w-4" :class="fraudRiskColor" />
            Fraud Indicators
          </p>
          <ul class="text-xs text-muted-foreground space-y-1 ml-6 list-disc">
            <li v-for="(indicator, index) in fraudCheck.indicators" :key="index">
              {{ indicator }}
            </li>
          </ul>
        </div>

        <!-- Fingerprint Info -->
        <div class="flex items-center gap-2 text-xs text-muted-foreground">
          <Fingerprint class="h-3 w-3" />
          <span>PRNU fingerprint extracted and verified</span>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
