<script setup lang="ts">
import { ref, computed } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { Users, TrendingUp, TrendingDown, AlertTriangle, BarChart3 } from 'lucide-vue-next'
import ConsensusIndicator from './ConsensusIndicator.vue'

interface JudgeScore {
  judge_id: number
  judge_name?: string
  score: number
  is_outlier: boolean
}

interface Props {
  submissionId: number
  judgeCount: number
  scoreMean?: number
  scoreStd?: number
  iccValue?: number
  consensusVerdict?: string
  outlierJudges?: number[]
  outlierScores?: number[]
  flaggedForReview?: boolean
  confidenceLevel?: number
  judgeScores?: JudgeScore[]
}

const props = defineProps<Props>()

const showDetails = ref(false)

const iccPercentage = computed(() => {
  return props.iccValue ? props.iccValue * 100 : 0
})

const consensusQuality = computed(() => {
  if (!props.iccValue) return 'unknown'
  if (props.iccValue >= 0.75) return 'excellent'
  if (props.iccValue >= 0.60) return 'good'
  if (props.iccValue >= 0.40) return 'fair'
  return 'poor'
})

const consensusColor = computed(() => {
  switch (props.consensusVerdict) {
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

const scoreRange = computed(() => {
  if (!props.judgeScores || props.judgeScores.length === 0) return { min: 0, max: 10 }
  const scores = props.judgeScores.map(j => j.score)
  return {
    min: Math.min(...scores),
    max: Math.max(...scores)
  }
})
</script>

<template>
  <Card>
    <CardHeader>
      <div class="flex items-center justify-between">
        <CardTitle class="flex items-center gap-2">
          <Users class="h-5 w-5" />
          Judge Consensus Analysis
        </CardTitle>
        <button
          @click="showDetails = !showDetails"
          class="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          {{ showDetails ? 'Hide' : 'Show' }} Details
        </button>
      </div>
      <CardDescription>
        Inter-rater reliability and score agreement
      </CardDescription>
    </CardHeader>

    <CardContent class="space-y-4">
      <!-- Consensus Indicator -->
      <ConsensusIndicator
        :icc="iccValue"
        :verdict="consensusVerdict"
        :judge-count="judgeCount"
        :outlier-count="outlierJudges?.length || 0"
        :flagged-for-review="flaggedForReview"
        size="md"
      />

      <!-- Poor Consensus Alert -->
      <Alert v-if="consensusVerdict === 'poor_consensus' || flaggedForReview" variant="destructive">
        <AlertTriangle class="h-4 w-4" />
        <AlertDescription>
          <div class="space-y-2">
            <p class="font-semibold">Manual Review Recommended</p>
            <p class="text-sm">
              {{ outlierJudges && outlierJudges.length > 0
                ? `${outlierJudges.length} judge(s) scored significantly different from others.`
                : 'Judges showed poor agreement on this submission.' }}
            </p>
            <p class="text-sm">
              ICC: {{ iccValue?.toFixed(2) || 'N/A' }} (threshold: 0.40 for acceptable consensus)
            </p>
          </div>
        </AlertDescription>
      </Alert>

      <!-- Details Section -->
      <div v-if="showDetails" class="space-y-4 pt-2 border-t">
        <!-- ICC Score -->
        <div v-if="iccValue !== undefined" class="space-y-2">
          <div class="flex items-center justify-between text-sm">
            <span class="text-muted-foreground">Intraclass Correlation (ICC)</span>
            <span :class="['font-medium', consensusColor]">
              {{ iccValue.toFixed(3) }}
            </span>
          </div>
          <Progress :model-value="iccPercentage" class="h-2" />
          <div class="flex justify-between text-xs text-muted-foreground">
            <span>Poor (0.0)</span>
            <span :class="['capitalize font-medium', consensusColor]">{{ consensusQuality }}</span>
            <span>Perfect (1.0)</span>
          </div>
        </div>

        <!-- Score Statistics -->
        <div v-if="scoreMean !== undefined" class="grid grid-cols-2 gap-4">
          <div class="space-y-1">
            <p class="text-xs text-muted-foreground">Mean Score</p>
            <p class="text-2xl font-bold">{{ scoreMean.toFixed(1) }}</p>
          </div>
          <div class="space-y-1">
            <p class="text-xs text-muted-foreground">Std Deviation</p>
            <p class="text-2xl font-bold">{{ scoreStd?.toFixed(2) || 'N/A' }}</p>
          </div>
        </div>

        <!-- Score Range -->
        <div class="space-y-2">
          <p class="text-sm font-medium">Score Range</p>
          <div class="flex items-center gap-2 text-sm">
            <span class="text-muted-foreground">{{ scoreRange.min.toFixed(1) }}</span>
            <Progress :model-value="(scoreRange.max / 10) * 100" class="h-2" />
            <span class="text-muted-foreground">{{ scoreRange.max.toFixed(1) }}</span>
          </div>
          <p class="text-xs text-muted-foreground">
            Range: {{ (scoreRange.max - scoreRange.min).toFixed(1) }} points
            <span v-if="(scoreRange.max - scoreRange.min) > 3" class="text-amber-600 dark:text-amber-400">
              (High variance)
            </span>
          </p>
        </div>

        <!-- Individual Judge Scores -->
        <div v-if="judgeScores && judgeScores.length > 0" class="space-y-2">
          <p class="text-sm font-medium">Individual Scores</p>
          <div class="space-y-2">
            <div
              v-for="judge in judgeScores"
              :key="judge.judge_id"
              class="flex items-center justify-between p-2 rounded-lg bg-muted/50"
            >
              <div class="flex items-center gap-2">
                <span class="text-sm">Judge {{ judge.judge_id }}</span>
                <Badge v-if="judge.is_outlier" variant="destructive" class="text-xs">
                  Outlier
                </Badge>
              </div>
              <span class="text-sm font-medium">{{ judge.score.toFixed(1) }}/10</span>
            </div>
          </div>
        </div>

        <!-- Outlier Explanation -->
        <div v-if="outlierJudges && outlierJudges.length > 0" class="space-y-1">
          <p class="text-sm font-medium flex items-center gap-2">
            <AlertTriangle class="h-4 w-4 text-red-600 dark:text-red-400" />
            Outlier Detection
          </p>
          <p class="text-xs text-muted-foreground">
            Judge(s) {{ outlierJudges.join(', ') }} scored more than 2 standard deviations
            from the mean, indicating potential bias or different interpretation standards.
          </p>
        </div>

        <!-- Confidence Level -->
        <div v-if="confidenceLevel !== undefined" class="space-y-1">
          <p class="text-sm font-medium">Confidence Level</p>
          <Progress :model-value="confidenceLevel * 100" class="h-2" />
          <p class="text-xs text-muted-foreground">
            {{ (confidenceLevel * 100).toFixed(0) }}% confidence in consensus verdict
          </p>
        </div>

        <!-- ICC Interpretation -->
        <div class="space-y-1 text-xs text-muted-foreground bg-muted/30 p-3 rounded-lg">
          <p class="font-medium text-foreground">ICC Interpretation:</p>
          <ul class="ml-4 space-y-1">
            <li>≥ 0.75: Strong consensus</li>
            <li>0.60-0.74: Moderate consensus</li>
            <li>0.40-0.59: Weak consensus</li>
            <li>&lt; 0.40: Poor consensus (review recommended)</li>
          </ul>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
