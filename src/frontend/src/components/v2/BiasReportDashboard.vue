<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { BarChart3, TrendingDown, TrendingUp, AlertTriangle, Users, CheckCircle } from 'lucide-vue-next'
import axios from 'axios'

interface JudgeProfile {
  judge_id: number
  submission_count: number
  avg_score: number
  bias_score: number
  bias_category: string
  consistency_score: number
}

interface FlaggedSubmission {
  submission_id: number
  icc_value: number
  consensus_verdict: string
  outlier_judges: number[]
}

interface BiasReport {
  competition_id: number
  total_judges: number
  avg_bias_score: number
  bias_std_dev: number
  avg_consistency: number
  flagged_submissions_count: number
  judge_profiles: JudgeProfile[]
  flagged_submissions: FlaggedSubmission[]
}

interface Props {
  competitionId: number
}

const props = defineProps<Props>()

const loading = ref(false)
const error = ref('')
const report = ref<BiasReport | null>(null)

const loadReport = async () => {
  try {
    loading.value = true
    error.value = ''
    const response = await axios.get(
      `/api/v1/judges-analytics/competition/${props.competitionId}/bias-report`
    )
    report.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load bias report'
  } finally {
    loading.value = false
  }
}

const biasDistribution = computed(() => {
  if (!report.value) return { harsh: 0, neutral: 0, lenient: 0 }

  const dist = { harsh: 0, neutral: 0, lenient: 0 }
  report.value.judge_profiles.forEach(profile => {
    if (profile.bias_category === 'harsh') dist.harsh++
    else if (profile.bias_category === 'lenient') dist.lenient++
    else dist.neutral++
  })
  return dist
})

const consistencyLevel = computed(() => {
  if (!report.value) return 'unknown'
  const avg = report.value.avg_consistency
  if (avg >= 0.8) return 'excellent'
  if (avg >= 0.6) return 'good'
  if (avg >= 0.4) return 'fair'
  return 'poor'
})

const overallHealth = computed(() => {
  if (!report.value) return 'unknown'

  const avgBias = Math.abs(report.value.avg_bias_score)
  const consistency = report.value.avg_consistency
  const flaggedRate = report.value.total_judges > 0
    ? report.value.flagged_submissions_count / report.value.total_judges
    : 0

  // Good: low bias, high consistency, few flagged
  if (avgBias < 0.5 && consistency > 0.7 && flaggedRate < 0.2) return 'healthy'
  // Concerning: moderate issues
  if (avgBias < 1.0 && consistency > 0.5 && flaggedRate < 0.4) return 'moderate'
  // Poor: significant issues
  return 'concerning'
})

const healthColor = computed(() => {
  switch (overallHealth.value) {
    case 'healthy':
      return 'text-green-600 dark:text-green-400'
    case 'moderate':
      return 'text-yellow-600 dark:text-yellow-400'
    case 'concerning':
      return 'text-red-600 dark:text-red-400'
    default:
      return 'text-gray-600 dark:text-gray-400'
  }
})

const sortedProfiles = computed(() => {
  if (!report.value) return []
  return [...report.value.judge_profiles].sort((a, b) => Math.abs(b.bias_score) - Math.abs(a.bias_score))
})

onMounted(() => {
  loadReport()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold">Judge Bias Report</h2>
        <p class="text-sm text-muted-foreground">
          Competition bias analysis and consensus quality metrics
        </p>
      </div>
      <Button @click="loadReport" :disabled="loading" size="sm">
        <BarChart3 class="h-4 w-4 mr-2" />
        {{ loading ? 'Loading...' : 'Refresh' }}
      </Button>
    </div>

    <!-- Error Alert -->
    <Alert v-if="error" variant="destructive">
      <AlertTriangle class="h-4 w-4" />
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <!-- Loading State -->
    <div v-if="loading && !report" class="flex items-center justify-center py-12">
      <div class="text-center space-y-2">
        <BarChart3 class="h-8 w-8 animate-pulse mx-auto text-muted-foreground" />
        <p class="text-sm text-muted-foreground">Loading bias report...</p>
      </div>
    </div>

    <!-- Report Content -->
    <div v-else-if="report" class="space-y-6">
      <!-- Overall Health Card -->
      <Card>
        <CardHeader>
          <CardTitle>Competition Health Overview</CardTitle>
          <CardDescription>Overall judging quality metrics</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <!-- Total Judges -->
            <div class="space-y-1">
              <div class="flex items-center gap-1 text-sm text-muted-foreground">
                <Users class="h-4 w-4" />
                <span>Total Judges</span>
              </div>
              <p class="text-3xl font-bold">{{ report.total_judges }}</p>
            </div>

            <!-- Average Bias -->
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">Avg Bias Score</p>
              <p class="text-3xl font-bold" :class="Math.abs(report.avg_bias_score) > 1.0 ? 'text-amber-600' : ''">
                {{ report.avg_bias_score.toFixed(2) }}
              </p>
              <p class="text-xs text-muted-foreground">
                ± {{ report.bias_std_dev.toFixed(2) }}
              </p>
            </div>

            <!-- Average Consistency -->
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">Avg Consistency</p>
              <p class="text-3xl font-bold">{{ (report.avg_consistency * 100).toFixed(0) }}%</p>
              <Badge :variant="consistencyLevel === 'excellent' || consistencyLevel === 'good' ? 'default' : 'secondary'">
                {{ consistencyLevel }}
              </Badge>
            </div>

            <!-- Flagged Submissions -->
            <div class="space-y-1">
              <div class="flex items-center gap-1 text-sm text-muted-foreground">
                <AlertTriangle class="h-4 w-4" />
                <span>Flagged</span>
              </div>
              <p class="text-3xl font-bold" :class="report.flagged_submissions_count > 0 ? 'text-red-600' : ''">
                {{ report.flagged_submissions_count }}
              </p>
              <p class="text-xs text-muted-foreground">Submissions</p>
            </div>
          </div>

          <!-- Overall Health Status -->
          <div class="mt-4 p-4 rounded-lg bg-muted/50">
            <div class="flex items-center gap-2">
              <component
                :is="overallHealth === 'healthy' ? CheckCircle : AlertTriangle"
                :class="['h-5 w-5', healthColor]"
              />
              <span class="font-semibold capitalize" :class="healthColor">
                {{ overallHealth }} Judging Environment
              </span>
            </div>
            <p class="text-sm text-muted-foreground mt-1">
              <template v-if="overallHealth === 'healthy'">
                Judges show good agreement and consistent scoring patterns. No major concerns.
              </template>
              <template v-else-if="overallHealth === 'moderate'">
                Some bias detected but within acceptable ranges. Monitor for improvements.
              </template>
              <template v-else>
                Significant bias or poor consensus detected. Consider judge training or score review.
              </template>
            </p>
          </div>
        </CardContent>
      </Card>

      <!-- Bias Distribution -->
      <Card>
        <CardHeader>
          <CardTitle>Bias Distribution</CardTitle>
          <CardDescription>Judge scoring tendencies</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-3 gap-4">
            <div class="flex flex-col items-center p-4 rounded-lg bg-red-500/10">
              <TrendingDown class="h-6 w-6 text-red-600 dark:text-red-400 mb-2" />
              <p class="text-2xl font-bold">{{ biasDistribution.harsh }}</p>
              <p class="text-sm text-muted-foreground">Harsh</p>
            </div>
            <div class="flex flex-col items-center p-4 rounded-lg bg-blue-500/10">
              <CheckCircle class="h-6 w-6 text-blue-600 dark:text-blue-400 mb-2" />
              <p class="text-2xl font-bold">{{ biasDistribution.neutral }}</p>
              <p class="text-sm text-muted-foreground">Neutral</p>
            </div>
            <div class="flex flex-col items-center p-4 rounded-lg bg-green-500/10">
              <TrendingUp class="h-6 w-6 text-green-600 dark:text-green-400 mb-2" />
              <p class="text-2xl font-bold">{{ biasDistribution.lenient }}</p>
              <p class="text-sm text-muted-foreground">Lenient</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Judge Profiles -->
      <Card>
        <CardHeader>
          <CardTitle>Individual Judge Profiles</CardTitle>
          <CardDescription>Sorted by bias magnitude (most biased first)</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="space-y-3">
            <div
              v-for="profile in sortedProfiles"
              :key="profile.judge_id"
              class="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted/70 transition-colors"
            >
              <div class="flex items-center gap-3">
                <div class="flex flex-col">
                  <span class="font-semibold">Judge {{ profile.judge_id }}</span>
                  <span class="text-xs text-muted-foreground">
                    {{ profile.submission_count }} submissions scored
                  </span>
                </div>
                <Badge
                  :variant="profile.bias_category === 'neutral' ? 'default' : 'secondary'"
                  :class="{
                    'bg-red-500/10 text-red-600 dark:text-red-400': profile.bias_category === 'harsh',
                    'bg-green-500/10 text-green-600 dark:text-green-400': profile.bias_category === 'lenient'
                  }"
                >
                  {{ profile.bias_category }}
                </Badge>
              </div>

              <div class="flex items-center gap-4 text-sm">
                <div class="text-right">
                  <p class="text-muted-foreground">Avg Score</p>
                  <p class="font-medium">{{ profile.avg_score.toFixed(1) }}/10</p>
                </div>
                <div class="text-right">
                  <p class="text-muted-foreground">Bias</p>
                  <p class="font-medium" :class="Math.abs(profile.bias_score) > 2.0 ? 'text-red-600' : ''">
                    {{ profile.bias_score > 0 ? '+' : '' }}{{ profile.bias_score.toFixed(2) }}
                  </p>
                </div>
                <div class="text-right">
                  <p class="text-muted-foreground">Consistency</p>
                  <p class="font-medium">{{ (profile.consistency_score * 100).toFixed(0) }}%</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Flagged Submissions -->
      <Card v-if="report.flagged_submissions.length > 0">
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <AlertTriangle class="h-5 w-5 text-amber-600" />
            Flagged Submissions ({{ report.flagged_submissions.length }})
          </CardTitle>
          <CardDescription>Submissions with poor judge consensus</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="space-y-3">
            <div
              v-for="submission in report.flagged_submissions"
              :key="submission.submission_id"
              class="flex items-center justify-between p-3 rounded-lg bg-amber-500/10 border border-amber-500/20"
            >
              <div>
                <p class="font-semibold">Submission #{{ submission.submission_id }}</p>
                <p class="text-sm text-muted-foreground">
                  {{ submission.outlier_judges.length }} outlier judge(s) detected
                </p>
              </div>
              <div class="text-right">
                <p class="text-sm text-muted-foreground">ICC</p>
                <p class="text-lg font-bold text-red-600">{{ submission.icc_value.toFixed(2) }}</p>
                <Badge variant="destructive" class="text-xs">{{ submission.consensus_verdict }}</Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
