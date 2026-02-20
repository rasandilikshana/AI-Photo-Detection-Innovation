<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Gavel, Calendar, Camera, CheckCircle, XCircle, Image, Clock, ArrowLeft,
  BarChart3, ShieldCheck, ShieldAlert, ShieldQuestion, AlertTriangle,
  Eye, Star, FileCheck, Loader2, FileImage, Fingerprint, Globe,
  History, Network, Monitor, User as UserIcon, RefreshCw
} from 'lucide-vue-next'
import apiClient from '@/api/client'

interface JudgeAssignment {
  assignment_id: number
  competition_id: number
  competition_title: string
  competition_status: string
  submission_start: string
  submission_end: string
}

interface CompetitionStats {
  competition_id: number
  competition_title: string
  competition_status: string
  total_submissions: number
  approved_submissions: number
  scored_by_me: number
  pending_to_score: number
  status_breakdown: Record<string, number>
  verdict_breakdown: Record<string, number>
}

interface JudgeSubmission {
  id: number
  title: string
  description: string
  jpg_file_url: string
  status: string
  verification_verdict: string | null
  verification_confidence: number | null
  ai_summary: {
    verdict: string
    confidence_score: number
    layer1_verdict: string | null
    layer2_verdict: string | null
    layer2_confidence: number | null
    layer3_verdict: string | null
    layer3_confidence: number | null
    raw_linkage_verdict: string | null
  } | null
  camera_make: string
  camera_model: string
  iso: number | null
  aperture: string | null
  shutter_speed: string | null
  total_score: number
  score_count: number
  is_scored_by_me: boolean
  created_at: string
}

interface ScoreAuditLog {
  id: number
  action_type: 'create' | 'update' | 'delete'
  composition_score: number | null
  technical_score: number | null
  creativity_score: number | null
  overall_score: number | null
  comments: string | null
  prev_composition_score: number | null
  prev_technical_score: number | null
  prev_creativity_score: number | null
  prev_overall_score: number | null
  prev_comments: string | null
  ip_address: string | null
  user_agent: string | null
  session_id: string | null
  judge_identifier: string | null
  score_id: number | null
  submission_id: number
  judge_id: number
  competition_id: number
  created_at: string
}

interface AuditLogListResponse {
  logs: ScoreAuditLog[]
  total_count: number
  unique_sessions: number
  unique_ips: number
}

const router = useRouter()
const authStore = useAuthStore()

const assignments = ref<JudgeAssignment[]>([])
const selectedCompetition = ref<number | null>(null)
const competitionStats = ref<CompetitionStats | null>(null)
const submissions = ref<JudgeSubmission[]>([])
const isLoading = ref(true)
const isLoadingStats = ref(false)
const isLoadingSubmissions = ref(false)
const error = ref('')

// Filter state
const statusFilter = ref<string>('all')
const verdictFilter = ref<string>('all')
const scoredFilter = ref<string>('all')

// Audit log state
const showAuditLogs = ref(false)
const auditLogs = ref<ScoreAuditLog[]>([])
const auditLogStats = ref<{ total_count: number; unique_sessions: number; unique_ips: number } | null>(null)
const isLoadingAuditLogs = ref(false)

// Check if user is a judge
const isJudge = computed(() => {
  return authStore.user?.role === 'judge' || authStore.user?.role === 'admin'
})

// Filtered submissions based on current filters
const filteredSubmissions = computed(() => {
  return submissions.value.filter(sub => {
    // Status filter
    if (statusFilter.value !== 'all' && sub.status !== statusFilter.value) return false
    // Verdict filter
    if (verdictFilter.value !== 'all' && sub.verification_verdict !== verdictFilter.value) return false
    // Scored filter
    if (scoredFilter.value === 'scored' && !sub.is_scored_by_me) return false
    if (scoredFilter.value === 'unscored' && sub.is_scored_by_me) return false
    return true
  })
})

onMounted(async () => {
  if (!isJudge.value) {
    router.push('/')
    return
  }

  try {
    isLoading.value = true
    error.value = ''
    const response = await apiClient.get('/scores/my-assignments')
    assignments.value = response.data
  } catch (err: unknown) {
    error.value = 'Failed to load judge assignments'
    console.error('Failed to load assignments:', err)
  } finally {
    isLoading.value = false
  }
})

const loadCompetitionData = async (competitionId: number) => {
  selectedCompetition.value = competitionId
  statusFilter.value = 'all'
  verdictFilter.value = 'all'
  scoredFilter.value = 'all'

  // Load stats and submissions in parallel
  isLoadingStats.value = true
  isLoadingSubmissions.value = true

  try {
    const [statsResponse, submissionsResponse] = await Promise.all([
      apiClient.get(`/scores/competition/${competitionId}/stats`),
      apiClient.get(`/scores/competition/${competitionId}/submissions`),
    ])
    competitionStats.value = statsResponse.data
    submissions.value = submissionsResponse.data
  } catch (err) {
    error.value = 'Failed to load competition data'
    console.error('Failed to load competition data:', err)
  } finally {
    isLoadingStats.value = false
    isLoadingSubmissions.value = false
  }
}

const goBackToAssignments = () => {
  selectedCompetition.value = null
  competitionStats.value = null
  submissions.value = []
  showAuditLogs.value = false
  auditLogs.value = []
  auditLogStats.value = null
}

const loadAuditLogs = async () => {
  if (!selectedCompetition.value) return

  isLoadingAuditLogs.value = true
  try {
    const response = await apiClient.get<AuditLogListResponse>(
      `/scores/audit-logs/competition/${selectedCompetition.value}`
    )
    auditLogs.value = response.data.logs
    auditLogStats.value = {
      total_count: response.data.total_count,
      unique_sessions: response.data.unique_sessions,
      unique_ips: response.data.unique_ips,
    }
  } catch (err) {
    console.error('Failed to load audit logs:', err)
    error.value = 'Failed to load scoring activity logs'
  } finally {
    isLoadingAuditLogs.value = false
  }
}

const toggleAuditLogs = async () => {
  showAuditLogs.value = !showAuditLogs.value
  if (showAuditLogs.value && auditLogs.value.length === 0) {
    await loadAuditLogs()
  }
}

const getActionTypeVariant = (actionType: string) => {
  const variants: Record<string, string> = {
    create: 'default',
    update: 'secondary',
    delete: 'destructive',
  }
  return variants[actionType] || 'outline'
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

const truncateUserAgent = (ua: string | null) => {
  if (!ua) return 'Unknown'
  // Extract browser name from user agent
  if (ua.includes('Chrome')) return 'Chrome'
  if (ua.includes('Firefox')) return 'Firefox'
  if (ua.includes('Safari')) return 'Safari'
  if (ua.includes('Edge')) return 'Edge'
  return ua.length > 30 ? ua.substring(0, 30) + '...' : ua
}

const getStatusVariant = (status: string) => {
  const variants: Record<string, string> = {
    open: 'default',
    judging: 'secondary',
    closed: 'destructive',
    completed: 'outline',
  }
  return variants[status] || 'secondary'
}

const getSubmissionStatusVariant = (status: string) => {
  const variants: Record<string, string> = {
    approved: 'default',
    pending: 'secondary',
    analyzing: 'outline',
    rejected: 'destructive',
  }
  return variants[status] || 'secondary'
}

const getVerdictVariant = (verdict: string | null) => {
  if (!verdict) return 'outline'
  const variants: Record<string, string> = {
    authentic: 'default',
    suspicious: 'secondary',
    ai_generated: 'destructive',
    needs_review: 'outline',
  }
  return variants[verdict] || 'outline'
}

const getVerdictIcon = (verdict: string | null) => {
  if (!verdict) return ShieldQuestion
  const icons: Record<string, typeof ShieldCheck> = {
    authentic: ShieldCheck,
    suspicious: ShieldAlert,
    ai_generated: AlertTriangle,
    needs_review: ShieldQuestion,
  }
  return icons[verdict] || ShieldQuestion
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const formatConfidence = (confidence: number | null) => {
  if (confidence === null || confidence === undefined) return 'N/A'
  return `${(confidence * 100).toFixed(0)}%`
}

// Convert verdict to PASS/FAIL display
const getLayerStatus = (verdict: string | null) => {
  if (!verdict) return { status: 'PENDING', isPass: null }
  const upperVerdict = verdict.toUpperCase()
  if (['AUTHENTIC', 'PASS', 'LINKED', 'VALID'].includes(upperVerdict)) {
    return { status: 'PASS', isPass: true }
  }
  if (['REJECT', 'FAIL', 'AI_GENERATED', 'INVALID'].includes(upperVerdict)) {
    return { status: 'FAIL', isPass: false }
  }
  if (['QUARANTINE', 'SUSPICIOUS', 'NEEDS_REVIEW'].includes(upperVerdict)) {
    return { status: 'REVIEW', isPass: null }
  }
  return { status: verdict.toUpperCase(), isPass: null }
}

const getImageUrl = (url: string) => {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  const baseUrl = import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '') || 'http://localhost:8080'
  return `${baseUrl}${url}`
}
</script>

<template>
  <div class="container mx-auto px-4 md:px-6 py-6 md:py-10">
    <!-- Header -->
    <div class="mb-6 md:mb-8">
      <div class="flex items-center gap-3 mb-2">
        <div class="w-10 h-10 md:w-12 md:h-12 rounded-xl bg-primary/10 flex items-center justify-center">
          <Gavel class="w-5 h-5 md:w-6 md:h-6 text-primary" />
        </div>
        <div>
          <h1 class="text-2xl md:text-3xl font-bold text-foreground">Judge Dashboard</h1>
          <p class="text-sm md:text-lg text-muted-foreground">
            Review and score submissions for your assigned competitions
          </p>
        </div>
      </div>
    </div>

    <!-- Not a judge warning -->
    <Alert v-if="!isJudge" variant="destructive" class="mb-6">
      <AlertDescription>
        You don't have judge permissions. Please contact an administrator.
      </AlertDescription>
    </Alert>

    <!-- Error alert -->
    <Alert v-if="error" variant="destructive" class="mb-6">
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <!-- Loading state -->
    <div v-if="isLoading" class="text-center py-20">
      <Loader2 class="w-12 h-12 text-primary animate-spin mx-auto mb-6" />
      <p class="text-muted-foreground text-lg">Loading your assignments...</p>
    </div>

    <template v-else-if="isJudge && !selectedCompetition">
      <!-- No assignments -->
      <div v-if="assignments.length === 0" class="text-center py-20">
        <div class="w-24 h-24 rounded-full bg-muted flex items-center justify-center mx-auto mb-6">
          <Gavel class="w-12 h-12 text-muted-foreground" />
        </div>
        <p class="text-xl text-muted-foreground">You are not assigned to any competitions yet.</p>
        <p class="text-muted-foreground mt-2">Contact an administrator to be assigned as a judge.</p>
      </div>

      <!-- Assignments grid -->
      <div v-else>
        <h2 class="text-xl font-semibold mb-4">Your Assigned Competitions</h2>
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card
            v-for="assignment in assignments"
            :key="assignment.assignment_id"
            class="cursor-pointer hover:shadow-lg transition-all hover:border-primary/50"
            @click="loadCompetitionData(assignment.competition_id)"
          >
            <CardHeader>
              <div class="flex justify-between items-start mb-2">
                <Badge :variant="getStatusVariant(assignment.competition_status)">
                  {{ assignment.competition_status.toUpperCase() }}
                </Badge>
              </div>
              <CardTitle class="line-clamp-2">
                {{ assignment.competition_title }}
              </CardTitle>
              <CardDescription class="flex items-center gap-2">
                <Calendar class="w-4 h-4" />
                {{ formatDate(assignment.submission_start) }} - {{ formatDate(assignment.submission_end) }}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" class="w-full">
                <Eye class="w-4 h-4 mr-2" />
                View Submissions
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </template>

    <!-- Competition Detail View -->
    <template v-else-if="isJudge && selectedCompetition">
      <!-- Back button -->
      <div class="mb-6">
        <Button variant="ghost" @click="goBackToAssignments" class="group">
          <ArrowLeft class="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" />
          Back to Competitions
        </Button>
      </div>

      <!-- Stats Loading -->
      <div v-if="isLoadingStats" class="text-center py-12">
        <Loader2 class="w-10 h-10 text-primary animate-spin mx-auto mb-4" />
        <p class="text-muted-foreground">Loading competition statistics...</p>
      </div>

      <!-- Stats Cards -->
      <div v-else-if="competitionStats" class="mb-8">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-2xl font-bold">{{ competitionStats.competition_title }}</h2>
          <Badge :variant="getStatusVariant(competitionStats.competition_status)" class="text-sm">
            {{ competitionStats.competition_status.toUpperCase() }}
          </Badge>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent class="pt-6">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                  <BarChart3 class="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <p class="text-2xl font-bold">{{ competitionStats.total_submissions }}</p>
                  <p class="text-sm text-muted-foreground">Total Submissions</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent class="pt-6">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                  <FileCheck class="w-5 h-5 text-green-500" />
                </div>
                <div>
                  <p class="text-2xl font-bold">{{ competitionStats.approved_submissions }}</p>
                  <p class="text-sm text-muted-foreground">Approved</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent class="pt-6">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Star class="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p class="text-2xl font-bold">{{ competitionStats.scored_by_me }}</p>
                  <p class="text-sm text-muted-foreground">Scored by You</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent class="pt-6">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                  <Clock class="w-5 h-5 text-orange-500" />
                </div>
                <div>
                  <p class="text-2xl font-bold">{{ competitionStats.pending_to_score }}</p>
                  <p class="text-sm text-muted-foreground">Pending to Score</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- AI Verdict Breakdown -->
        <Card class="mb-6">
          <CardHeader class="pb-3">
            <CardTitle class="text-lg">AI Verification Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="flex flex-wrap gap-4">
              <div v-if="competitionStats.verdict_breakdown.authentic" class="flex items-center gap-2">
                <ShieldCheck class="w-5 h-5 text-green-500" />
                <span class="font-medium">{{ competitionStats.verdict_breakdown.authentic }}</span>
                <span class="text-muted-foreground">Authentic</span>
              </div>
              <div v-if="competitionStats.verdict_breakdown.suspicious" class="flex items-center gap-2">
                <ShieldAlert class="w-5 h-5 text-yellow-500" />
                <span class="font-medium">{{ competitionStats.verdict_breakdown.suspicious }}</span>
                <span class="text-muted-foreground">Suspicious</span>
              </div>
              <div v-if="competitionStats.verdict_breakdown.ai_generated" class="flex items-center gap-2">
                <AlertTriangle class="w-5 h-5 text-red-500" />
                <span class="font-medium">{{ competitionStats.verdict_breakdown.ai_generated }}</span>
                <span class="text-muted-foreground">AI Generated</span>
              </div>
              <div v-if="competitionStats.verdict_breakdown.needs_review" class="flex items-center gap-2">
                <ShieldQuestion class="w-5 h-5 text-blue-500" />
                <span class="font-medium">{{ competitionStats.verdict_breakdown.needs_review }}</span>
                <span class="text-muted-foreground">Needs Review</span>
              </div>
              <div v-if="competitionStats.verdict_breakdown.none" class="flex items-center gap-2">
                <Loader2 class="w-5 h-5 text-muted-foreground" />
                <span class="font-medium">{{ competitionStats.verdict_breakdown.none }}</span>
                <span class="text-muted-foreground">Pending Analysis</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Scoring Activity Toggle Button -->
        <div class="flex justify-end mb-4">
          <Button
            variant="outline"
            @click="toggleAuditLogs"
            :disabled="isLoadingAuditLogs"
          >
            <History v-if="!isLoadingAuditLogs" class="w-4 h-4 mr-2" />
            <Loader2 v-else class="w-4 h-4 mr-2 animate-spin" />
            {{ showAuditLogs ? 'Hide Scoring Activity' : 'View Scoring Activity' }}
          </Button>
        </div>

        <!-- Scoring Activity Logs Panel -->
        <Card v-if="showAuditLogs" class="mb-6">
          <CardHeader>
            <div class="flex items-center justify-between">
              <div>
                <CardTitle class="flex items-center gap-2">
                  <History class="w-5 h-5" />
                  Scoring Activity Log
                </CardTitle>
                <CardDescription>
                  Track all scoring actions with client details for shared credentials testing
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" @click="loadAuditLogs" :disabled="isLoadingAuditLogs">
                <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isLoadingAuditLogs }" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <!-- Audit Stats Summary -->
            <div v-if="auditLogStats" class="grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4 mb-6">
              <div class="p-3 md:p-4 bg-muted rounded-lg text-center">
                <p class="text-xl md:text-2xl font-bold">{{ auditLogStats.total_count }}</p>
                <p class="text-xs md:text-sm text-muted-foreground">Total Actions</p>
              </div>
              <div class="p-3 md:p-4 bg-muted rounded-lg text-center">
                <p class="text-xl md:text-2xl font-bold">{{ auditLogStats.unique_ips }}</p>
                <p class="text-xs md:text-sm text-muted-foreground flex items-center justify-center gap-1">
                  <Network class="w-3 h-3" /> Unique IPs
                </p>
              </div>
              <div class="p-3 md:p-4 bg-muted rounded-lg text-center">
                <p class="text-xl md:text-2xl font-bold">{{ auditLogStats.unique_sessions }}</p>
                <p class="text-xs md:text-sm text-muted-foreground flex items-center justify-center gap-1">
                  <Monitor class="w-3 h-3" /> Unique Sessions
                </p>
              </div>
            </div>

            <!-- Loading State -->
            <div v-if="isLoadingAuditLogs" class="text-center py-8">
              <Loader2 class="w-8 h-8 text-primary animate-spin mx-auto mb-2" />
              <p class="text-muted-foreground">Loading activity logs...</p>
            </div>

            <!-- No Logs -->
            <div v-else-if="auditLogs.length === 0" class="text-center py-8">
              <History class="w-12 h-12 text-muted-foreground mx-auto mb-2" />
              <p class="text-muted-foreground">No scoring activity recorded yet.</p>
            </div>

            <!-- Audit Logs List -->
            <div v-else class="space-y-3 max-h-96 overflow-y-auto">
              <div
                v-for="log in auditLogs"
                :key="log.id"
                class="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div class="flex items-start justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <Badge :variant="getActionTypeVariant(log.action_type)">
                      {{ log.action_type.toUpperCase() }}
                    </Badge>
                    <span class="text-sm text-muted-foreground">
                      Submission #{{ log.submission_id }}
                    </span>
                  </div>
                  <span class="text-xs text-muted-foreground">
                    {{ formatDateTime(log.created_at) }}
                  </span>
                </div>

                <!-- Score Values -->
                <div v-if="log.action_type !== 'delete'" class="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3 text-sm">
                  <div>
                    <span class="text-muted-foreground">Composition:</span>
                    <span class="ml-1 font-medium">{{ log.composition_score?.toFixed(1) || 'N/A' }}</span>
                  </div>
                  <div>
                    <span class="text-muted-foreground">Technical:</span>
                    <span class="ml-1 font-medium">{{ log.technical_score?.toFixed(1) || 'N/A' }}</span>
                  </div>
                  <div>
                    <span class="text-muted-foreground">Creativity:</span>
                    <span class="ml-1 font-medium">{{ log.creativity_score?.toFixed(1) || 'N/A' }}</span>
                  </div>
                  <div>
                    <span class="text-muted-foreground">Overall:</span>
                    <span class="ml-1 font-bold text-primary">{{ log.overall_score?.toFixed(2) || 'N/A' }}</span>
                  </div>
                </div>

                <!-- Previous Values for Updates -->
                <div v-if="log.action_type === 'update' && log.prev_overall_score" class="text-xs text-muted-foreground mb-2">
                  Previous: {{ log.prev_composition_score?.toFixed(1) }} / {{ log.prev_technical_score?.toFixed(1) }} / {{ log.prev_creativity_score?.toFixed(1) }} = {{ log.prev_overall_score?.toFixed(2) }}
                </div>

                <!-- Client Info -->
                <div class="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                  <div class="flex items-center gap-1">
                    <Network class="w-3 h-3" />
                    <span>{{ log.ip_address || 'Unknown IP' }}</span>
                  </div>
                  <div class="flex items-center gap-1">
                    <Monitor class="w-3 h-3" />
                    <span>{{ truncateUserAgent(log.user_agent) }}</span>
                  </div>
                  <div v-if="log.judge_identifier" class="flex items-center gap-1">
                    <UserIcon class="w-3 h-3" />
                    <span class="font-medium text-foreground">{{ log.judge_identifier }}</span>
                  </div>
                </div>

                <!-- Comments -->
                <div v-if="log.comments" class="mt-2 text-sm italic text-muted-foreground border-l-2 border-muted pl-2">
                  "{{ log.comments }}"
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Filters -->
      <div class="mb-6 space-y-3">
        <!-- Status Filter -->
        <div class="flex flex-col sm:flex-row sm:items-center gap-2">
          <span class="text-sm font-medium shrink-0">Status:</span>
          <div class="flex gap-1 flex-wrap">
            <Button
              v-for="status in ['all', 'approved', 'pending', 'analyzing', 'rejected']"
              :key="status"
              size="sm"
              class="text-xs md:text-sm"
              :variant="statusFilter === status ? 'default' : 'outline'"
              @click="statusFilter = status"
            >
              {{ status === 'all' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1) }}
            </Button>
          </div>
        </div>

        <!-- Verdict Filter -->
        <div class="flex flex-col sm:flex-row sm:items-center gap-2">
          <span class="text-sm font-medium shrink-0">AI Verdict:</span>
          <div class="flex gap-1 flex-wrap">
            <Button
              v-for="verdict in ['all', 'authentic', 'suspicious', 'needs_review', 'ai_generated']"
              :key="verdict"
              size="sm"
              class="text-xs md:text-sm"
              :variant="verdictFilter === verdict ? 'default' : 'outline'"
              @click="verdictFilter = verdict"
            >
              {{ verdict === 'all' ? 'All' : verdict.replace('_', ' ').split(' ').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') }}
            </Button>
          </div>
        </div>

        <!-- Scored Filter -->
        <div class="flex flex-col sm:flex-row sm:items-center gap-2">
          <span class="text-sm font-medium shrink-0">Scoring:</span>
          <div class="flex gap-1 flex-wrap">
            <Button
              v-for="scored in ['all', 'unscored', 'scored']"
              :key="scored"
              size="sm"
              class="text-xs md:text-sm"
              :variant="scoredFilter === scored ? 'default' : 'outline'"
              @click="scoredFilter = scored"
            >
              {{ scored === 'all' ? 'All' : scored.charAt(0).toUpperCase() + scored.slice(1) }}
            </Button>
          </div>
        </div>
      </div>

      <!-- Submissions Loading -->
      <div v-if="isLoadingSubmissions" class="text-center py-12">
        <Loader2 class="w-10 h-10 text-primary animate-spin mx-auto mb-4" />
        <p class="text-muted-foreground">Loading submissions...</p>
      </div>

      <!-- No Submissions -->
      <div v-else-if="filteredSubmissions.length === 0" class="text-center py-12">
        <div class="w-20 h-20 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
          <Image class="w-10 h-10 text-muted-foreground" />
        </div>
        <p class="text-lg text-muted-foreground">
          No submissions match your filters.
        </p>
      </div>

      <!-- Submissions Grid -->
      <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          v-for="submission in filteredSubmissions"
          :key="submission.id"
          class="overflow-hidden hover:shadow-lg transition-all"
          :class="{ 'border-green-500/50 bg-green-500/5': submission.is_scored_by_me }"
        >
          <!-- Thumbnail -->
          <div class="aspect-[4/3] bg-muted relative overflow-hidden">
            <img
              v-if="submission.jpg_file_url"
              :src="getImageUrl(submission.jpg_file_url)"
              :alt="submission.title"
              class="w-full h-full object-cover"
              @error="(e) => { (e.target as HTMLImageElement).style.display = 'none' }"
            />
            <div v-else class="w-full h-full flex items-center justify-center">
              <Image class="w-12 h-12 text-muted-foreground" />
            </div>

            <!-- Status overlay badges -->
            <div class="absolute top-2 left-2 flex gap-2">
              <Badge :variant="getSubmissionStatusVariant(submission.status)" class="text-xs">
                {{ submission.status.toUpperCase() }}
              </Badge>
            </div>

            <!-- Scored indicator -->
            <div v-if="submission.is_scored_by_me" class="absolute top-2 right-2">
              <Badge variant="default" class="bg-green-500 text-xs">
                <CheckCircle class="w-3 h-3 mr-1" />
                Scored
              </Badge>
            </div>
          </div>

          <CardHeader class="pb-2">
            <CardTitle class="line-clamp-2 text-lg">
              {{ submission.title }}
            </CardTitle>

            <!-- AI Verdict Badge -->
            <div class="flex items-center gap-2 mt-2">
              <Badge :variant="getVerdictVariant(submission.verification_verdict)" class="gap-1">
                <component :is="getVerdictIcon(submission.verification_verdict)" class="w-3 h-3" />
                {{ submission.verification_verdict ? submission.verification_verdict.replace('_', ' ').toUpperCase() : 'PENDING' }}
              </Badge>
              <span v-if="submission.verification_confidence" class="text-lg font-bold"
                    :class="{
                      'text-green-500': getLayerStatus(submission.verification_verdict).isPass === true,
                      'text-red-500': getLayerStatus(submission.verification_verdict).isPass === false,
                      'text-yellow-500': getLayerStatus(submission.verification_verdict).isPass === null
                    }">
                {{ formatConfidence(submission.verification_confidence) }}
              </span>
            </div>

            <!-- Layer Analysis Mini-Preview -->
            <div v-if="submission.ai_summary" class="mt-3 space-y-1.5">
              <!-- Layer 1 -->
              <div v-if="submission.ai_summary.layer1_verdict" class="flex items-center justify-between text-xs">
                <div class="flex items-center gap-1.5">
                  <FileImage class="w-3 h-3 text-blue-500" />
                  <span class="text-muted-foreground">L1 Metadata</span>
                </div>
                <span class="font-semibold"
                      :class="{
                        'text-green-500': getLayerStatus(submission.ai_summary.layer1_verdict).isPass === true,
                        'text-red-500': getLayerStatus(submission.ai_summary.layer1_verdict).isPass === false,
                        'text-yellow-500': getLayerStatus(submission.ai_summary.layer1_verdict).isPass === null
                      }">
                  {{ getLayerStatus(submission.ai_summary.layer1_verdict).status }}
                </span>
              </div>
              <!-- Layer 2 -->
              <div v-if="submission.ai_summary.layer2_verdict" class="flex items-center justify-between text-xs">
                <div class="flex items-center gap-1.5">
                  <Fingerprint class="w-3 h-3 text-purple-500" />
                  <span class="text-muted-foreground">L2 Fingerprint</span>
                </div>
                <div class="flex items-center gap-1">
                  <span v-if="submission.ai_summary.layer2_confidence" class="text-muted-foreground">
                    {{ formatConfidence(submission.ai_summary.layer2_confidence) }}
                  </span>
                  <span class="font-semibold"
                        :class="{
                          'text-green-500': getLayerStatus(submission.ai_summary.layer2_verdict).isPass === true,
                          'text-red-500': getLayerStatus(submission.ai_summary.layer2_verdict).isPass === false,
                          'text-yellow-500': getLayerStatus(submission.ai_summary.layer2_verdict).isPass === null
                        }">
                    {{ getLayerStatus(submission.ai_summary.layer2_verdict).status }}
                  </span>
                </div>
              </div>
              <!-- Layer 3 -->
              <div v-if="submission.ai_summary.layer3_verdict" class="flex items-center justify-between text-xs">
                <div class="flex items-center gap-1.5">
                  <Globe class="w-3 h-3 text-cyan-500" />
                  <span class="text-muted-foreground">L3 API Check</span>
                </div>
                <div class="flex items-center gap-1">
                  <span v-if="submission.ai_summary.layer3_confidence" class="text-muted-foreground">
                    {{ formatConfidence(submission.ai_summary.layer3_confidence) }}
                  </span>
                  <span class="font-semibold"
                        :class="{
                          'text-green-500': getLayerStatus(submission.ai_summary.layer3_verdict).isPass === true,
                          'text-red-500': getLayerStatus(submission.ai_summary.layer3_verdict).isPass === false,
                          'text-yellow-500': getLayerStatus(submission.ai_summary.layer3_verdict).isPass === null
                        }">
                    {{ getLayerStatus(submission.ai_summary.layer3_verdict).status }}
                  </span>
                </div>
              </div>
            </div>
          </CardHeader>

          <CardContent>
            <!-- Camera Info -->
            <div v-if="submission.camera_make" class="flex items-center gap-2 text-sm text-muted-foreground mb-3">
              <Camera class="w-4 h-4" />
              {{ submission.camera_make }} {{ submission.camera_model }}
            </div>

            <!-- Score Info -->
            <div v-if="submission.score_count > 0" class="flex items-center gap-2 text-sm text-muted-foreground mb-3">
              <Star class="w-4 h-4" />
              Avg: {{ (submission.total_score / submission.score_count).toFixed(1) }} ({{ submission.score_count }} scores)
            </div>

            <!-- Submitted date -->
            <p class="text-xs text-muted-foreground mb-4 flex items-center gap-1">
              <Clock class="w-3 h-3" />
              {{ formatDate(submission.created_at) }}
            </p>

            <!-- Action Button -->
            <Button
              v-if="submission.status === 'approved' && !submission.is_scored_by_me"
              class="w-full"
              @click="router.push(`/judge/score/${submission.id}`)"
            >
              <Star class="w-4 h-4 mr-2" />
              Score This Entry
            </Button>
            <Button
              v-else-if="submission.is_scored_by_me"
              variant="outline"
              class="w-full"
              @click="router.push(`/judge/score/${submission.id}`)"
            >
              <Eye class="w-4 h-4 mr-2" />
              View Details
            </Button>
            <Button
              v-else
              variant="secondary"
              class="w-full"
              disabled
            >
              {{ submission.status === 'analyzing' ? 'Analyzing...' : 'Not Ready for Scoring' }}
            </Button>
          </CardContent>
        </Card>
      </div>
    </template>
  </div>
</template>
