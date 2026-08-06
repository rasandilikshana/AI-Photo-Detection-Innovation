<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Gavel, Calendar, Camera, CheckCircle, XCircle, Image, Clock, ArrowLeft,
  BarChart3, ShieldCheck, ShieldAlert, ShieldQuestion, AlertTriangle,
  Eye, Star, FileCheck, Loader2, FileImage, Fingerprint, Globe,
  History, Network, Monitor, User as UserIcon, RefreshCw, AlertCircle, ThumbsUp, ThumbsDown,
  ChevronDown, Filter, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight
} from 'lucide-vue-next'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import apiClient from '@/api/client'
import { useV2AnalyticsStore } from '@/stores/v2Analytics'
import { JudgeProfileBadge, ConsensusAnalysisCard } from '@/components/v2'

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
  analysis_error: string | null
  rejection_reason: string | null
  reviewed_by: number | null
  reviewed_at: string | null
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
const route = useRoute()
const authStore = useAuthStore()
const v2Analytics = useV2AnalyticsStore()

const assignments = ref<JudgeAssignment[]>([])
const selectedCompetition = ref<number | null>(null)
const selectedCompetitionTitle = ref<string>('')
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

// Pagination state
const currentPage = ref(1)
const itemsPerPage = ref(12)

// Audit log state
const showAuditLogs = ref(false)
const auditLogs = ref<ScoreAuditLog[]>([])
const auditLogStats = ref<{ total_count: number; unique_sessions: number; unique_ips: number } | null>(null)
const isLoadingAuditLogs = ref(false)

// Review dialog state
const showReviewDialog = ref(false)
const reviewSubmissionId = ref<number | null>(null)
const reviewAction = ref<'approve' | 'reject'>('approve')
const reviewReason = ref('')
const isSubmittingReview = ref(false)

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

// Pagination computed
const totalPages = computed(() => Math.ceil(filteredSubmissions.value.length / itemsPerPage.value))

const paginatedSubmissions = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return filteredSubmissions.value.slice(start, end)
})

// Reset page when filters change
watch([statusFilter, verdictFilter, scoredFilter], () => {
  currentPage.value = 1
})

// Watch for route changes (handles navigation between /judge and /judge/competition/:id)
watch(() => route.params.competitionId, async (newCompetitionId, oldCompetitionId) => {
  // If navigating from competition view to main judge panel
  if (oldCompetitionId && !newCompetitionId) {
    // Reset to assignments view
    selectedCompetition.value = null
    selectedCompetitionTitle.value = ''
    competitionStats.value = null
    submissions.value = []
    showAuditLogs.value = false
    auditLogs.value = []
    auditLogStats.value = null
    currentPage.value = 1
  }
  // If navigating to a different competition
  else if (newCompetitionId && newCompetitionId !== oldCompetitionId) {
    const id = Number(newCompetitionId)
    const assignment = assignments.value.find(a => a.competition_id === id)
    if (assignment) {
      selectedCompetitionTitle.value = assignment.competition_title
      await loadCompetitionData(id, false)
    }
  }
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

    // Check if we have a competitionId in the route
    const competitionId = route.params.competitionId
    if (competitionId) {
      const id = Number(competitionId)
      // Find the assignment to get the title
      const assignment = assignments.value.find(a => a.competition_id === id)
      if (assignment) {
        selectedCompetitionTitle.value = assignment.competition_title
        await loadCompetitionData(id, false) // Don't update URL since we're already there
      }
    }
  } catch (err: unknown) {
    error.value = 'Failed to load judge assignments'
    console.error('Failed to load assignments:', err)
  } finally {
    isLoading.value = false
  }
})

const loadCompetitionData = async (competitionId: number, updateUrl: boolean = true) => {
  selectedCompetition.value = competitionId
  statusFilter.value = 'all'
  verdictFilter.value = 'all'
  scoredFilter.value = 'all'
  currentPage.value = 1

  // Update the URL to include competition ID (for back navigation)
  if (updateUrl) {
    router.replace(`/judge/competition/${competitionId}`)
  }

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
    selectedCompetitionTitle.value = competitionStats.value?.competition_title || ''
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
  selectedCompetitionTitle.value = ''
  competitionStats.value = null
  submissions.value = []
  showAuditLogs.value = false
  auditLogs.value = []
  auditLogStats.value = null
  // Update URL to main judge page
  router.replace('/judge')
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

const openReviewDialog = (submissionId: number, action: 'approve' | 'reject') => {
  reviewSubmissionId.value = submissionId
  reviewAction.value = action
  reviewReason.value = ''
  showReviewDialog.value = true
}

const closeReviewDialog = () => {
  showReviewDialog.value = false
  reviewSubmissionId.value = null
  reviewReason.value = ''
}

const submitReview = async () => {
  if (!reviewSubmissionId.value) return
  if (reviewAction.value === 'reject' && !reviewReason.value.trim()) {
    error.value = 'Please provide a reason for rejection'
    return
  }

  isSubmittingReview.value = true
  error.value = ''

  try {
    const params = new URLSearchParams({
      action: reviewAction.value,
    })
    if (reviewAction.value === 'reject') {
      params.append('reason', reviewReason.value.trim())
    }

    await apiClient.post(`/scores/review/${reviewSubmissionId.value}?${params.toString()}`)

    // Update the submission in the local state
    const index = submissions.value.findIndex(s => s.id === reviewSubmissionId.value)
    if (index !== -1) {
      submissions.value[index].status = reviewAction.value === 'approve' ? 'approved' : 'rejected'
      if (reviewAction.value === 'reject') {
        submissions.value[index].rejection_reason = reviewReason.value.trim()
      }
    }

    closeReviewDialog()
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : 'Failed to submit review'
    error.value = errorMessage
    console.error('Failed to submit review:', err)
  } finally {
    isSubmittingReview.value = false
  }
}

const getImageUrl = (url: string) => {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  // Extract just the filename and return as /uploads/filename
  const filename = url.split('/').pop() || url
  return `/uploads/${filename}`
}
</script>

<template>
  <div class="container mx-auto px-4 md:px-6 py-6 md:py-10">
    <!-- Header -->
    <div class="mb-6 md:mb-8">
      <span class="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
        <span class="h-1.5 w-1.5 rounded-full bg-brand"></span>
        Judge panel
      </span>
      <h1 class="mt-3 text-3xl md:text-4xl font-display font-semibold tracking-tight">Judge dashboard</h1>
      <p class="mt-2 text-muted-foreground">
        Review and score submissions for your assigned competitions.
      </p>
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
      <Loader2 class="w-8 h-8 animate-spin text-muted-foreground mx-auto mb-6" />
      <p class="text-muted-foreground text-lg">Loading your assignments...</p>
    </div>

    <template v-else-if="isJudge && !selectedCompetition">
      <!-- No assignments -->
      <div v-if="assignments.length === 0" class="text-center py-20">
        <div class="w-16 h-16 rounded-full bg-secondary flex items-center justify-center mx-auto mb-6">
          <Gavel class="w-8 h-8 text-muted-foreground" />
        </div>
        <p class="text-xl text-muted-foreground">You are not assigned to any competitions yet.</p>
        <p class="text-muted-foreground mt-2">Contact an administrator to be assigned as a judge.</p>
      </div>

      <!-- Assignments grid -->
      <div v-else>
        <h2 class="text-xl font-display font-semibold tracking-tight mb-4">Your assigned competitions</h2>
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card
            v-for="assignment in assignments"
            :key="assignment.assignment_id"
            class="rounded-2xl cursor-pointer transition-shadow hover:shadow-lg"
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
                View submissions
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
          Back to competitions
        </Button>
      </div>

      <!-- Stats Loading -->
      <div v-if="isLoadingStats" class="text-center py-12">
        <Loader2 class="w-8 h-8 animate-spin text-muted-foreground mx-auto mb-4" />
        <p class="text-muted-foreground">Loading competition statistics...</p>
      </div>

      <!-- Stats Cards -->
      <div v-else-if="competitionStats" class="mb-8">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-2xl font-display font-semibold tracking-tight">{{ competitionStats.competition_title }}</h2>
            <!-- V2.0: Judge Profile Badge -->
            <JudgeProfileBadge
              v-if="authStore.user?.id && selectedCompetition"
              :judge-id="authStore.user.id"
              :competition-id="selectedCompetition"
              class="mt-2"
            />
          </div>
          <Badge :variant="getStatusVariant(competitionStats.competition_status)" class="text-sm">
            {{ competitionStats.competition_status.toUpperCase() }}
          </Badge>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="rounded-2xl border bg-card p-5">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
                <BarChart3 class="w-5 h-5 text-foreground" />
              </div>
              <div>
                <p class="text-3xl font-display font-semibold">{{ competitionStats.total_submissions }}</p>
                <p class="text-sm text-muted-foreground">Total submissions</p>
              </div>
            </div>
          </div>

          <div class="rounded-2xl border bg-card p-5">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-success/10 flex items-center justify-center">
                <FileCheck class="w-5 h-5 text-success" />
              </div>
              <div>
                <p class="text-3xl font-display font-semibold">{{ competitionStats.approved_submissions }}</p>
                <p class="text-sm text-muted-foreground">Approved</p>
              </div>
            </div>
          </div>

          <div class="rounded-2xl border bg-card p-5">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
                <Star class="w-5 h-5 text-foreground" />
              </div>
              <div>
                <p class="text-3xl font-display font-semibold">{{ competitionStats.scored_by_me }}</p>
                <p class="text-sm text-muted-foreground">Scored by you</p>
              </div>
            </div>
          </div>

          <div class="rounded-2xl border bg-card p-5">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-warning/10 flex items-center justify-center">
                <Clock class="w-5 h-5 text-warning" />
              </div>
              <div>
                <p class="text-3xl font-display font-semibold">{{ competitionStats.pending_to_score }}</p>
                <p class="text-sm text-muted-foreground">Awaiting your score</p>
              </div>
            </div>
          </div>
        </div>

        <!-- AI Verdict Breakdown -->
        <Card class="rounded-2xl mb-6">
          <CardHeader class="pb-3">
            <CardTitle class="text-lg">AI Verification Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="flex flex-wrap gap-4">
              <div v-if="competitionStats.verdict_breakdown.authentic" class="flex items-center gap-2">
                <ShieldCheck class="w-5 h-5 text-success" />
                <span class="font-medium">{{ competitionStats.verdict_breakdown.authentic }}</span>
                <span class="text-muted-foreground">Authentic</span>
              </div>
              <div v-if="competitionStats.verdict_breakdown.suspicious" class="flex items-center gap-2">
                <ShieldAlert class="w-5 h-5 text-warning" />
                <span class="font-medium">{{ competitionStats.verdict_breakdown.suspicious }}</span>
                <span class="text-muted-foreground">Suspicious</span>
              </div>
              <div v-if="competitionStats.verdict_breakdown.ai_generated" class="flex items-center gap-2">
                <AlertTriangle class="w-5 h-5 text-destructive" />
                <span class="font-medium">{{ competitionStats.verdict_breakdown.ai_generated }}</span>
                <span class="text-muted-foreground">AI Generated</span>
              </div>
              <div v-if="competitionStats.verdict_breakdown.needs_review" class="flex items-center gap-2">
                <ShieldQuestion class="w-5 h-5 text-info" />
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

        <!-- Filters and Scoring Activity Button Row -->
        <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
          <!-- Filter Dropdowns -->
          <div class="flex flex-wrap items-center gap-2">
            <Filter class="w-4 h-4 text-muted-foreground hidden sm:block" />

            <!-- Status Filter Dropdown -->
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" class="min-w-[110px] justify-between">
                  <span class="truncate">{{ statusFilter === 'all' ? 'All Status' : statusFilter.charAt(0).toUpperCase() + statusFilter.slice(1) }}</span>
                  <ChevronDown class="w-4 h-4 ml-2 shrink-0 opacity-50" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" class="w-40">
                <DropdownMenuRadioGroup v-model="statusFilter">
                  <DropdownMenuRadioItem value="all">All Status</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="approved">Approved</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="pending">Pending</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="analyzing">Analyzing</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="rejected">Rejected</DropdownMenuRadioItem>
                </DropdownMenuRadioGroup>
              </DropdownMenuContent>
            </DropdownMenu>

            <!-- AI Verdict Filter Dropdown -->
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" class="min-w-[130px] justify-between">
                  <span class="truncate">{{ verdictFilter === 'all' ? 'All Verdicts' : verdictFilter.replace('_', ' ').split(' ').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') }}</span>
                  <ChevronDown class="w-4 h-4 ml-2 shrink-0 opacity-50" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" class="w-44">
                <DropdownMenuRadioGroup v-model="verdictFilter">
                  <DropdownMenuRadioItem value="all">All Verdicts</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="authentic">Authentic</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="suspicious">Suspicious</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="needs_review">Needs Review</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="ai_generated">AI Generated</DropdownMenuRadioItem>
                </DropdownMenuRadioGroup>
              </DropdownMenuContent>
            </DropdownMenu>

            <!-- Scoring Filter Dropdown -->
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" class="min-w-[110px] justify-between">
                  <span class="truncate">{{ scoredFilter === 'all' ? 'All Scoring' : scoredFilter.charAt(0).toUpperCase() + scoredFilter.slice(1) }}</span>
                  <ChevronDown class="w-4 h-4 ml-2 shrink-0 opacity-50" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" class="w-36">
                <DropdownMenuRadioGroup v-model="scoredFilter">
                  <DropdownMenuRadioItem value="all">All Scoring</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="unscored">Unscored</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="scored">Scored</DropdownMenuRadioItem>
                </DropdownMenuRadioGroup>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <!-- Scoring Activity Button -->
          <Button
            variant="outline"
            @click="toggleAuditLogs"
            :disabled="isLoadingAuditLogs"
          >
            <History v-if="!isLoadingAuditLogs" class="w-4 h-4 mr-2" />
            <Loader2 v-else class="w-4 h-4 mr-2 animate-spin" />
            {{ showAuditLogs ? 'Hide scoring activity' : 'View scoring activity' }}
          </Button>
        </div>

        <!-- Scoring Activity Logs Panel -->
        <Card v-if="showAuditLogs" class="rounded-2xl mb-6">
          <CardHeader>
            <div class="flex items-center justify-between">
              <div>
                <CardTitle class="flex items-center gap-2">
                  <History class="w-5 h-5" />
                  Scoring Activity Log
                </CardTitle>
                <CardDescription>
                  Every scoring action with time, device, and network details.
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" aria-label="Refresh activity log" @click="loadAuditLogs" :disabled="isLoadingAuditLogs">
                <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isLoadingAuditLogs }" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <!-- Audit Stats Summary -->
            <div v-if="auditLogStats" class="grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4 mb-6">
              <div class="p-3 md:p-4 bg-muted rounded-xl text-center">
                <p class="text-xl md:text-2xl font-display font-semibold">{{ auditLogStats.total_count }}</p>
                <p class="text-xs md:text-sm text-muted-foreground">Total Actions</p>
              </div>
              <div class="p-3 md:p-4 bg-muted rounded-xl text-center">
                <p class="text-xl md:text-2xl font-display font-semibold">{{ auditLogStats.unique_ips }}</p>
                <p class="text-xs md:text-sm text-muted-foreground flex items-center justify-center gap-1">
                  <Network class="w-3 h-3" /> Unique IPs
                </p>
              </div>
              <div class="p-3 md:p-4 bg-muted rounded-xl text-center">
                <p class="text-xl md:text-2xl font-display font-semibold">{{ auditLogStats.unique_sessions }}</p>
                <p class="text-xs md:text-sm text-muted-foreground flex items-center justify-center gap-1">
                  <Monitor class="w-3 h-3" /> Unique Sessions
                </p>
              </div>
            </div>

            <!-- Loading State -->
            <div v-if="isLoadingAuditLogs" class="text-center py-8">
              <Loader2 class="w-8 h-8 animate-spin text-muted-foreground mx-auto mb-2" />
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

      <!-- Submissions Loading -->
      <div v-if="isLoadingSubmissions" class="text-center py-12">
        <Loader2 class="w-8 h-8 animate-spin text-muted-foreground mx-auto mb-4" />
        <p class="text-muted-foreground">Loading submissions...</p>
      </div>

      <!-- No Submissions -->
      <div v-else-if="filteredSubmissions.length === 0" class="text-center py-12">
        <div class="w-16 h-16 rounded-full bg-secondary flex items-center justify-center mx-auto mb-4">
          <Image class="w-8 h-8 text-muted-foreground" />
        </div>
        <p class="text-lg text-muted-foreground">
          No submissions match your filters.
        </p>
        <p class="text-muted-foreground mt-1">
          Clear filters to see every submission.
        </p>
      </div>

      <!-- Submissions Grid -->
      <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          v-for="submission in paginatedSubmissions"
          :key="submission.id"
          class="overflow-hidden rounded-2xl cursor-pointer transition-shadow hover:shadow-lg"
          :class="{ 'border-brand/50 bg-brand/5': submission.is_scored_by_me }"
          @click="router.push(`/judge/score/${submission.id}?competition=${selectedCompetition}`)"
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
              <Badge variant="brand" class="text-xs">
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
              <span v-if="submission.verification_confidence" class="text-lg font-display font-semibold"
                    :class="{
                      'text-success': getLayerStatus(submission.verification_verdict).isPass === true,
                      'text-destructive': getLayerStatus(submission.verification_verdict).isPass === false,
                      'text-warning': getLayerStatus(submission.verification_verdict).isPass === null
                    }">
                {{ formatConfidence(submission.verification_confidence) }}
              </span>
            </div>

            <!-- Layer Analysis Mini-Preview -->
            <div v-if="submission.ai_summary" class="mt-3 space-y-1.5">
              <!-- Layer 1 -->
              <div v-if="submission.ai_summary.layer1_verdict" class="flex items-center justify-between text-xs">
                <div class="flex items-center gap-1.5">
                  <FileImage class="w-3 h-3 text-muted-foreground" />
                  <span class="text-muted-foreground">L1 Metadata</span>
                </div>
                <span class="font-semibold"
                      :class="{
                        'text-success': getLayerStatus(submission.ai_summary.layer1_verdict).isPass === true,
                        'text-destructive': getLayerStatus(submission.ai_summary.layer1_verdict).isPass === false,
                        'text-warning': getLayerStatus(submission.ai_summary.layer1_verdict).isPass === null
                      }">
                  {{ getLayerStatus(submission.ai_summary.layer1_verdict).status }}
                </span>
              </div>
              <!-- Layer 2 -->
              <div v-if="submission.ai_summary.layer2_verdict" class="flex items-center justify-between text-xs">
                <div class="flex items-center gap-1.5">
                  <Fingerprint class="w-3 h-3 text-muted-foreground" />
                  <span class="text-muted-foreground">L2 Fingerprint</span>
                </div>
                <div class="flex items-center gap-1">
                  <span v-if="submission.ai_summary.layer2_confidence" class="text-muted-foreground">
                    {{ formatConfidence(submission.ai_summary.layer2_confidence) }}
                  </span>
                  <span class="font-semibold"
                        :class="{
                          'text-success': getLayerStatus(submission.ai_summary.layer2_verdict).isPass === true,
                          'text-destructive': getLayerStatus(submission.ai_summary.layer2_verdict).isPass === false,
                          'text-warning': getLayerStatus(submission.ai_summary.layer2_verdict).isPass === null
                        }">
                    {{ getLayerStatus(submission.ai_summary.layer2_verdict).status }}
                  </span>
                </div>
              </div>
              <!-- Layer 3 -->
              <div v-if="submission.ai_summary.layer3_verdict" class="flex items-center justify-between text-xs">
                <div class="flex items-center gap-1.5">
                  <Globe class="w-3 h-3 text-muted-foreground" />
                  <span class="text-muted-foreground">L3 API Check</span>
                </div>
                <div class="flex items-center gap-1">
                  <span v-if="submission.ai_summary.layer3_confidence" class="text-muted-foreground">
                    {{ formatConfidence(submission.ai_summary.layer3_confidence) }}
                  </span>
                  <span class="font-semibold"
                        :class="{
                          'text-success': getLayerStatus(submission.ai_summary.layer3_verdict).isPass === true,
                          'text-destructive': getLayerStatus(submission.ai_summary.layer3_verdict).isPass === false,
                          'text-warning': getLayerStatus(submission.ai_summary.layer3_verdict).isPass === null
                        }">
                    {{ getLayerStatus(submission.ai_summary.layer3_verdict).status }}
                  </span>
                </div>
              </div>
            </div>
          </CardHeader>

          <CardContent>
            <!-- Analysis Error Alert -->
            <Alert v-if="submission.analysis_error" variant="destructive" class="mb-3">
              <AlertCircle class="w-4 h-4" />
              <AlertDescription class="text-xs">
                <strong>Analysis Error:</strong> {{ submission.analysis_error }}
              </AlertDescription>
            </Alert>

            <!-- Rejection Reason Alert -->
            <Alert v-if="submission.rejection_reason" variant="destructive" class="mb-3">
              <XCircle class="w-4 h-4" />
              <AlertDescription class="text-xs">
                <strong>Rejected:</strong> {{ submission.rejection_reason }}
              </AlertDescription>
            </Alert>

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

            <!-- Action Buttons -->
            <!-- Score button for approved submissions -->
            <Button
              v-if="submission.status?.toLowerCase() === 'approved' && !submission.is_scored_by_me"
              class="w-full"
              @click.stop="router.push(`/judge/score/${submission.id}?competition=${selectedCompetition}`)"
            >
              <Star class="w-4 h-4 mr-2" />
              Score this entry
            </Button>

            <!-- View details for scored submissions -->
            <Button
              v-else-if="submission.is_scored_by_me"
              variant="outline"
              class="w-full"
              @click.stop="router.push(`/judge/score/${submission.id}?competition=${selectedCompetition}`)"
            >
              <Eye class="w-4 h-4 mr-2" />
              View details
            </Button>

            <!-- Manual review buttons for pending/needs_review/analysis_error submissions -->
            <div v-else-if="submission.status?.toLowerCase() === 'pending' || submission.verification_verdict?.toLowerCase() === 'needs_review' || submission.analysis_error" class="space-y-2">
              <div class="flex gap-2">
                <Button
                  variant="brand"
                  class="flex-1"
                  @click.stop="openReviewDialog(submission.id, 'approve')"
                >
                  <ThumbsUp class="w-4 h-4 mr-1" />
                  Approve
                </Button>
                <Button
                  variant="destructive"
                  class="flex-1"
                  @click.stop="openReviewDialog(submission.id, 'reject')"
                >
                  <ThumbsDown class="w-4 h-4 mr-1" />
                  Reject
                </Button>
              </div>
              <Button
                variant="outline"
                class="w-full"
                @click.stop="router.push(`/judge/score/${submission.id}?competition=${selectedCompetition}`)"
              >
                <Eye class="w-4 h-4 mr-2" />
                View full details
              </Button>
            </div>

            <!-- Not ready message for analyzing or rejected -->
            <Button
              v-else
              variant="secondary"
              class="w-full"
              @click.stop
              disabled
            >
              {{ submission.status?.toLowerCase() === 'analyzing' ? 'Analyzing...' : submission.status?.toLowerCase() === 'rejected' ? 'Rejected' : 'Not Ready for Scoring' }}
            </Button>
          </CardContent>
        </Card>
      </div>

      <!-- Pagination Controls -->
      <div v-if="filteredSubmissions.length > itemsPerPage" class="flex items-center justify-between mt-8 px-2">
        <div class="text-sm text-muted-foreground">
          Showing {{ (currentPage - 1) * itemsPerPage + 1 }} - {{ Math.min(currentPage * itemsPerPage, filteredSubmissions.length) }} of {{ filteredSubmissions.length }} submissions
        </div>
        <div class="flex items-center gap-1">
          <!-- First Page -->
          <Button
            variant="outline"
            size="icon"
            class="h-8 w-8"
            aria-label="First page"
            :disabled="currentPage === 1"
            @click="currentPage = 1"
          >
            <ChevronsLeft class="w-4 h-4" />
          </Button>
          <!-- Previous Page -->
          <Button
            variant="outline"
            size="icon"
            class="h-8 w-8"
            aria-label="Previous page"
            :disabled="currentPage === 1"
            @click="currentPage--"
          >
            <ChevronLeft class="w-4 h-4" />
          </Button>

          <!-- Page Numbers -->
          <div class="flex items-center gap-1 mx-2">
            <template v-for="page in totalPages" :key="page">
              <Button
                v-if="page === 1 || page === totalPages || (page >= currentPage - 1 && page <= currentPage + 1)"
                :variant="page === currentPage ? 'default' : 'outline'"
                size="sm"
                class="h-8 w-8 p-0"
                @click="currentPage = page"
              >
                {{ page }}
              </Button>
              <span
                v-else-if="page === currentPage - 2 || page === currentPage + 2"
                class="px-1 text-muted-foreground"
              >...</span>
            </template>
          </div>

          <!-- Next Page -->
          <Button
            variant="outline"
            size="icon"
            class="h-8 w-8"
            aria-label="Next page"
            :disabled="currentPage === totalPages"
            @click="currentPage++"
          >
            <ChevronRight class="w-4 h-4" />
          </Button>
          <!-- Last Page -->
          <Button
            variant="outline"
            size="icon"
            class="h-8 w-8"
            aria-label="Last page"
            :disabled="currentPage === totalPages"
            @click="currentPage = totalPages"
          >
            <ChevronsRight class="w-4 h-4" />
          </Button>
        </div>
      </div>
    </template>

    <!-- Review Dialog -->
    <Dialog :open="showReviewDialog" @update:open="closeReviewDialog">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {{ reviewAction === 'approve' ? 'Approve Submission' : 'Reject Submission' }}
          </DialogTitle>
          <DialogDescription>
            {{ reviewAction === 'approve'
              ? 'This will approve the submission for scoring. You can optionally add a note.'
              : 'Please provide a reason for rejecting this submission. This will be visible to the participant.'
            }}
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4 py-4">
          <div class="space-y-2">
            <Label :for="'review-reason'">
              {{ reviewAction === 'approve' ? 'Note (optional)' : 'Reason for rejection *' }}
            </Label>
            <Textarea
              id="review-reason"
              v-model="reviewReason"
              :placeholder="reviewAction === 'approve'
                ? 'Optional note for this approval...'
                : 'e.g., Invalid RAW file format, suspected AI manipulation, etc.'
              "
              rows="3"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" @click="closeReviewDialog" :disabled="isSubmittingReview">
            Cancel
          </Button>
          <Button
            :variant="reviewAction === 'approve' ? 'default' : 'destructive'"
            @click="submitReview"
            :disabled="isSubmittingReview || (reviewAction === 'reject' && !reviewReason.trim())"
          >
            <Loader2 v-if="isSubmittingReview" class="w-4 h-4 mr-2 animate-spin" />
            {{ reviewAction === 'approve' ? 'Approve' : 'Reject' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
