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

const energyQuality = computed(() => {
  if (!props.prnuEnergy) return 'unknown'
  if (props.prnuEnergy > 0.03) return 'excellent'
  if (props.prnuEnergy > 0.02) return 'good'
  if (props.prnuEnergy > 0.01) return 'fair'
  return 'poor'
})

const energyColor = computed(() => {
  switch (energyQuality.value) {
    case 'excellent':
    case 'good':
      return 'text-green-600 dark:text-green-400'
    case 'fair':
      return 'text-yellow-600 dark:text-yellow-400'
    case 'poor':
      return 'text-red-600 dark:text-red-400'
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
        <div v-if="prnuEnergy" class="space-y-2">
          <div class="flex items-center justify-between text-sm">
            <span class="text-muted-foreground">PRNU Energy</span>
            <span :class="['font-medium', energyColor]">
              {{ prnuEnergy.toFixed(4) }}
            </span>
          </div>
          <Progress :model-value="Math.min(prnuEnergy * 3333, 100)" class="h-2" />
          <p class="text-xs text-muted-foreground">
            Quality: <span :class="['capitalize', energyColor]">{{ energyQuality }}</span>
            <span v-if="prnuEnergy < 0.01"> - Possible AI-generated image</span>
          </p>
        </div>

        <!-- Trust Score Breakdown -->
        <div v-if="trustScore && trustScore > 0" class="space-y-2">
          <p class="text-sm font-medium">Trust Score Breakdown</p>
          <div class="space-y-1 text-xs text-muted-foreground">
            <div class="flex justify-between">
              <span>Pattern Similarity (50%)</span>
              <span>Contributing to score</span>
            </div>
            <div class="flex justify-between">
              <span>Historical Data (30%)</span>
              <span>Contributing to score</span>
            </div>
            <div class="flex justify-between">
              <span>Consistency (20%)</span>
              <span>Contributing to score</span>
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
