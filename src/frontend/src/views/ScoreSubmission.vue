<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import {
  ArrowLeft, Camera, Aperture, Clock, Gauge, Star, Sparkles, Target,
  ShieldCheck, ShieldAlert, ShieldQuestion, AlertTriangle, Loader2,
  CheckCircle, XCircle, Layers, Eye, Link, FileImage, Fingerprint, Globe,
  ChevronDown, ChevronUp, Info, Cpu, Waves, Grid3X3, ImageIcon, Hash, BarChart2,
  ThumbsUp, ThumbsDown, AlertCircle, ZoomIn, ZoomOut, X, Maximize2, RotateCw
} from 'lucide-vue-next'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import apiClient from '@/api/client'
import { useV2AnalyticsStore } from '@/stores/v2Analytics'
import { CameraReputationCard, ConsensusIndicator } from '@/components/v2'

interface MyScore {
  id: number
  composition_score: number
  technical_score: number
  creativity_score: number
  overall_score: number
  comments: string | null
}

interface SubmissionDetail {
  id: number
  title: string
  description: string
  jpg_file_url: string
  raw_file_url: string | null
  status: string
  verification_verdict: string | null
  verification_confidence: number | null
  verification_details: {
    verdict: string
    confidence_score: number
    timestamp: string
    processing_time_ms?: number
    layer1_result?: {
      verdict: string
      confidence?: number
      metadata_present?: boolean
      camera_fields_found?: number
      ai_signatures_found?: number
      camera_score?: number
      consistency_score?: number
      analysis?: string
      flags?: string[]
    }
    layer2_result?: {
      verdict: string
      confidence: number
      prnu_score?: number
      ela_score?: number
      fft_score?: number
      prnu_energy?: number
      ela_uniformity?: number
      fft_high_freq_ratio?: number
      analysis?: string
      flags?: string[]
    }
    layer3_result?: {
      verdict: string
      confidence: number
      analysis?: string
      flags?: string[]
    }
    raw_jpg_linkage?: {
      verdict: string
      confidence?: number
      phash_distance?: number
      ssim_score?: number
      histogram_correlation?: number
      analysis?: string
      flags?: string[]
      // Normalised to the RAW frame [x, y, w, h] so it can be drawn at any preview
      // size. null when no crop was confirmed.
      crop_rect_norm?: [number, number, number, number] | null
      crop_fraction?: number
      geometry?: {
        inliers: number
        inlier_ratio: number
        crop_like: boolean
        low_texture: boolean
        keypoints_raw: number
        keypoints_jpg: number
        reproj_error_px: number
        reason: string
      } | null
      arbitration?: { verdict: string; reasoning: string } | null
    }
    // Weighted 0-100 aggregation. This is the number that decides the verdict; the
    // per-signal breakdown is what a judge reads to understand why.
    authenticity?: {
      score: number
      band: string
      verdict: string
      action: string
      weight_evaluated: number
      signals: Array<{
        name: string
        weight: number
        score: number
        contribution: number
        evidence: string
      }>
      missing: string[]
    } | null
    flags?: string[]
  } | null
  verification_timestamp: string | null
  camera_make: string
  camera_model: string
  lens_model: string | null
  iso: number
  aperture: string
  shutter_speed: string
  capture_date: string | null
  total_score: number
  score_count: number
  competition: {
    id: number
    title: string
    status: string
  } | null
  my_score: MyScore | null
  created_at: string
  // Review/error fields
  analysis_error: string | null
  rejection_reason: string | null
  reviewed_by: number | null
  reviewed_at: string | null
}

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const v2Analytics = useV2AnalyticsStore()

const submissionId = Number(route.params.submissionId)
const competitionId = route.query.competition ? Number(route.query.competition) : null

// Back navigation URL - go to specific competition if available
const backUrl = computed(() => {
  if (competitionId) {
    return `/judge/competition/${competitionId}`
  }
  return '/judge'
})

const submission = ref<SubmissionDetail | null>(null)
const compositionScore = ref<number>(5)
const technicalScore = ref<number>(5)
const creativityScore = ref<number>(5)
const comments = ref('')
const judgeIdentifier = ref('')  // Optional identifier for shared credentials tracking
const isLoading = ref(true)
const isSubmitting = ref(false)
const error = ref('')
const success = ref('')
const alreadyScored = ref(false)

// Track expanded layer sections
const expandedLayers = ref<Record<string, boolean>>({
  layer1: false,
  layer2: false,
  layer3: false,
  rawLinkage: false,
})

// Review dialog state
const showReviewDialog = ref(false)
const reviewAction = ref<'approve' | 'reject'>('approve')
const reviewReason = ref('')
const isSubmittingReview = ref(false)

// RAW preview state (browsers cannot render RAW — a derived JPEG is fetched from the API)
const rawPreviewUrl = ref<string | null>(null)
const rawPreviewStatus = ref<'idle' | 'loading' | 'ready' | 'unavailable'>('idle')

// Image lightbox state
const showImageLightbox = ref(false)
const lightboxSrc = ref('')
const lightboxLabel = ref('')
const imageZoom = ref(1)
const imageRotation = ref(0)
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const imagePosition = ref({ x: 0, y: 0 })

// Compute display name avoiding duplicates like "Canon Canon EOS 600D"
const cameraDisplayName = computed(() => {
  if (!submission.value) return ''
  const make = submission.value.camera_make?.trim() || ''
  const model = submission.value.camera_model?.trim() || ''

  if (!make && !model) return ''
  if (!make) return model
  if (!model) return make

  // If model already starts with make, just show model
  if (model.toLowerCase().startsWith(make.toLowerCase())) {
    return model
  }

  return `${make} ${model}`
})

// Check if submission needs manual review
const needsManualReview = computed(() => {
  if (!submission.value) return false
  const status = submission.value.status?.toLowerCase()
  const verdict = submission.value.verification_verdict?.toLowerCase()
  return status === 'pending' || verdict === 'needs_review' || !!submission.value.analysis_error
})

// Can the submission be scored (must be approved first)
const canBeScored = computed(() => {
  if (!submission.value) return false
  return submission.value.status?.toLowerCase() === 'approved'
})

// Check if submission is already approved (for corrective actions)
const isApproved = computed(() => {
  if (!submission.value) return false
  return submission.value.status?.toLowerCase() === 'approved'
})

// Check if submission is already rejected (for corrective actions)
const isRejected = computed(() => {
  if (!submission.value) return false
  return submission.value.status?.toLowerCase() === 'rejected'
})

const toggleLayer = (layer: string) => {
  expandedLayers.value[layer] = !expandedLayers.value[layer]
}

// Calculate overall score preview
const overallScorePreview = computed(() => {
  return (
    compositionScore.value * 0.4 +
    technicalScore.value * 0.3 +
    creativityScore.value * 0.3
  ).toFixed(2)
})

// Check if user is a judge
const isJudge = computed(() => {
  return authStore.user?.role === 'judge' || authStore.user?.role === 'admin'
})

onMounted(async () => {
  if (!isJudge.value) {
    router.push('/')
    return
  }

  try {
    isLoading.value = true
    error.value = ''
    // Use the judge-specific endpoint that includes full AI analysis
    const response = await apiClient.get(`/scores/submission-detail/${submissionId}`)
    submission.value = response.data

    // If already scored, populate the form with existing values
    if (response.data.my_score) {
      alreadyScored.value = true
      compositionScore.value = response.data.my_score.composition_score
      technicalScore.value = response.data.my_score.technical_score
      creativityScore.value = response.data.my_score.creativity_score
      comments.value = response.data.my_score.comments || ''
    }

    // Kick off RAW preview generation in the background (non-blocking)
    loadRawPreview()
  } catch (err) {
    error.value = 'Failed to load submission details'
    console.error('Failed to load submission:', err)
  } finally {
    isLoading.value = false
  }
})

const handleSubmit = async () => {
  if (!submission.value) return

  try {
    isSubmitting.value = true
    error.value = ''
    success.value = ''

    if (alreadyScored.value && submission.value.my_score) {
      // Update existing score
      await apiClient.put(`/scores/${submission.value.my_score.id}`, {
        composition_score: compositionScore.value,
        technical_score: technicalScore.value,
        creativity_score: creativityScore.value,
        comments: comments.value || null,
        judge_identifier: judgeIdentifier.value || null,
      })
      success.value = 'Score updated successfully!'
    } else {
      // Create new score
      await apiClient.post(`/scores/${submissionId}`, {
        composition_score: compositionScore.value,
        technical_score: technicalScore.value,
        creativity_score: creativityScore.value,
        comments: comments.value || null,
        judge_identifier: judgeIdentifier.value || null,
      })
      success.value = 'Score submitted successfully!'
    }

    setTimeout(() => {
      router.push('/judge')
    }, 1500)
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'response' in err) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      error.value = axiosErr.response?.data?.detail || 'Failed to submit score'
    } else {
      error.value = 'Failed to submit score'
    }
  } finally {
    isSubmitting.value = false
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

const getVerdictVariant = (verdict: string | null) => {
  if (!verdict) return 'outline'
  const variants: Record<string, string> = {
    authentic: 'default',
    AUTHENTIC: 'default',
    suspicious: 'secondary',
    QUARANTINE: 'secondary',
    ai_generated: 'destructive',
    REJECT: 'destructive',
    needs_review: 'outline',
  }
  return variants[verdict] || 'outline'
}

const getVerdictIcon = (verdict: string | null) => {
  if (!verdict) return ShieldQuestion
  const icons: Record<string, typeof ShieldCheck> = {
    authentic: ShieldCheck,
    AUTHENTIC: ShieldCheck,
    suspicious: ShieldAlert,
    QUARANTINE: ShieldAlert,
    ai_generated: AlertTriangle,
    REJECT: AlertTriangle,
    needs_review: ShieldQuestion,
  }
  return icons[verdict] || ShieldQuestion
}

const formatConfidence = (confidence: number | null | undefined) => {
  if (confidence === null || confidence === undefined) return 'N/A'
  return `${(confidence * 100).toFixed(0)}%`
}

// Convert verdict to PASS/FAIL display
const getPassFailStatus = (verdict: string | undefined) => {
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

// Get status badge color class
const getStatusColorClass = (isPass: boolean | null) => {
  if (isPass === true) return 'bg-success/10 text-success border-success/30'
  if (isPass === false) return 'bg-destructive/10 text-destructive border-destructive/30'
  return 'bg-warning/10 text-warning border-warning/30'
}

// Get status icon color class
const getStatusIconClass = (isPass: boolean | null) => {
  if (isPass === true) return 'text-success'
  if (isPass === false) return 'text-destructive'
  return 'text-warning'
}

// Get score bar color based on value
const getScoreBarColor = (score: number) => {
  if (score >= 0.7) return 'bg-success'
  if (score >= 0.4) return 'bg-warning'
  return 'bg-destructive'
}

// Format score as percentage
// Authenticity Score bands mirror AuthenticityScorer.BANDS in the backend. Kept in the
// same order so the colour always matches the action the backend reported.
const scoreBandClass = (score: number) => {
  if (score >= 75) return 'border-success bg-success/5'
  if (score >= 50) return 'border-warning bg-warning/5'
  if (score >= 25) return 'border-warning bg-warning/10'
  return 'border-destructive bg-destructive/5'
}

const SIGNAL_LABELS: Record<string, string> = {
  raw_provenance: 'RAW provenance',
  geometric_linkage: 'RAW↔JPG geometric linkage',
  metadata: 'Metadata integrity',
  prnu: 'Sensor fingerprint (PRNU)',
  frequency: 'Frequency distribution',
  third_party: 'Third-party AI detection',
  compression: 'Compression history',
}

const signalLabel = (name: string) => SIGNAL_LABELS[name] ?? name

// The crop rectangle is normalised to the RAW frame, so it can be drawn as
// percentages over the preview at whatever size the preview renders.
const cropRect = computed(() => {
  const rect = submission.value?.verification_details?.raw_jpg_linkage?.crop_rect_norm
  if (!rect || rect.length !== 4) return null
  const [x, y, w, h] = rect
  // A full-frame rectangle means the JPG is the whole RAW; drawing a box around the
  // entire image tells the judge nothing.
  if (w >= 0.995 && h >= 0.995) return null
  return {
    left: `${x * 100}%`,
    top: `${y * 100}%`,
    width: `${w * 100}%`,
    height: `${h * 100}%`,
  }
})

const formatScore = (score: number | undefined | null) => {
  if (score === undefined || score === null) return 'N/A'
  return `${(score * 100).toFixed(0)}%`
}

const scoreCategories = [
  {
    id: 'composition',
    label: 'Composition',
    weight: '40%',
    icon: Target,
    description: 'Framing, balance, rule of thirds, leading lines',
    model: compositionScore,
  },
  {
    id: 'technical',
    label: 'Technical Skill',
    weight: '30%',
    icon: Gauge,
    description: 'Focus, exposure, lighting, color accuracy',
    model: technicalScore,
  },
  {
    id: 'creativity',
    label: 'Creativity',
    weight: '30%',
    icon: Sparkles,
    description: 'Originality, artistic vision, emotional impact',
    model: creativityScore,
  },
]

// Review dialog functions
const openReviewDialog = (action: 'approve' | 'reject') => {
  reviewAction.value = action
  reviewReason.value = ''
  showReviewDialog.value = true
}

const closeReviewDialog = () => {
  showReviewDialog.value = false
  reviewReason.value = ''
}

const submitReview = async () => {
  if (!submission.value) return
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

    await apiClient.post(`/scores/review/${submission.value.id}?${params.toString()}`)

    // Update the local submission state
    submission.value.status = reviewAction.value === 'approve' ? 'approved' : 'rejected'
    if (reviewAction.value === 'reject') {
      submission.value.rejection_reason = reviewReason.value.trim()
    } else {
      submission.value.rejection_reason = null
    }

    closeReviewDialog()
    success.value = `Submission ${reviewAction.value}d successfully!`
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : 'Failed to submit review'
    error.value = errorMessage
    console.error('Failed to submit review:', err)
  } finally {
    isSubmittingReview.value = false
  }
}

// RAW preview loading
const rawExtension = computed(() => {
  const url = submission.value?.raw_file_url
  if (!url) return ''
  const ext = url.split('.').pop() || ''
  return ext.toUpperCase()
})

const loadRawPreview = async () => {
  if (!submission.value?.raw_file_url) return
  rawPreviewStatus.value = 'loading'
  try {
    const response = await apiClient.get(`/scores/raw-preview/${submissionId}`)
    rawPreviewUrl.value = response.data.preview_url
    rawPreviewStatus.value = 'ready'
  } catch (err) {
    console.error('Failed to load RAW preview:', err)
    rawPreviewStatus.value = 'unavailable'
  }
}

// Image lightbox functions
const openImageLightbox = (src: string, label: string) => {
  lightboxSrc.value = src
  lightboxLabel.value = label
  showImageLightbox.value = true
  imageZoom.value = 1
  imageRotation.value = 0
  imagePosition.value = { x: 0, y: 0 }
}

const closeImageLightbox = () => {
  showImageLightbox.value = false
}

const zoomIn = () => {
  if (imageZoom.value < 5) {
    imageZoom.value = Math.min(5, imageZoom.value + 0.1)
  }
}

const zoomOut = () => {
  if (imageZoom.value > 0.25) {
    imageZoom.value = Math.max(0.25, imageZoom.value - 0.1)
  }
}

const resetZoom = () => {
  imageZoom.value = 1
  imagePosition.value = { x: 0, y: 0 }
}

const rotateImage = () => {
  imageRotation.value = (imageRotation.value + 90) % 360
}

const handleWheel = (e: WheelEvent) => {
  e.preventDefault()
  if (e.deltaY < 0) {
    zoomIn()
  } else {
    zoomOut()
  }
}

const handleMouseDown = (e: MouseEvent) => {
  if (imageZoom.value > 1) {
    isDragging.value = true
    dragStart.value = { x: e.clientX - imagePosition.value.x, y: e.clientY - imagePosition.value.y }
  }
}

const handleMouseMove = (e: MouseEvent) => {
  if (isDragging.value && imageZoom.value > 1) {
    imagePosition.value = {
      x: e.clientX - dragStart.value.x,
      y: e.clientY - dragStart.value.y
    }
  }
}

const handleMouseUp = () => {
  isDragging.value = false
}

const handleKeydown = (e: KeyboardEvent) => {
  if (!showImageLightbox.value) return
  if (e.key === 'Escape') closeImageLightbox()
  if (e.key === '+' || e.key === '=') zoomIn()
  if (e.key === '-') zoomOut()
  if (e.key === '0') resetZoom()
  if (e.key === 'r') rotateImage()
}

// Add keyboard listener
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', handleKeydown)
}
</script>

<template>
  <div class="container mx-auto px-4 md:px-6 py-6 md:py-10 max-w-6xl">
    <div class="mb-4 md:mb-6">
      <Button variant="ghost" size="sm" @click="router.push(backUrl)" class="group">
        <ArrowLeft class="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" />
        Back to dashboard
      </Button>
    </div>

    <!-- Loading state -->
    <div v-if="isLoading" class="text-center py-20">
      <Loader2 class="w-8 h-8 animate-spin text-muted-foreground mx-auto mb-6" />
      <p class="text-muted-foreground text-lg">Loading submission...</p>
    </div>

    <!-- Error alert -->
    <Alert v-else-if="error && !submission" variant="destructive" class="mb-6">
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <template v-else-if="submission">
      <!-- Already scored banner -->
      <Alert v-if="alreadyScored" class="mb-6 bg-success/10 border-success/30">
        <CheckCircle class="w-4 h-4 text-success" />
        <AlertDescription class="text-success">
          You have already scored this submission. You can update your scores below.
        </AlertDescription>
      </Alert>

      <!-- Manual Review Required Banner -->
      <div v-if="needsManualReview && !canBeScored" class="mb-6 space-y-4">
        <!-- Analysis Error Alert -->
        <Alert v-if="submission.analysis_error" variant="destructive">
          <AlertCircle class="w-4 h-4" />
          <AlertDescription>
            <strong>Analysis Error:</strong> {{ submission.analysis_error }}
            <p class="text-xs mt-1 opacity-80">This submission requires manual review by a judge.</p>
          </AlertDescription>
        </Alert>

        <!-- Needs Review Alert -->
        <Alert v-else-if="submission.verification_verdict?.toLowerCase() === 'needs_review'" class="border-warning/40 bg-warning/10">
          <ShieldQuestion class="w-4 h-4 text-warning" />
          <AlertDescription class="text-warning">
            <strong>Manual Review Required:</strong> The AI verification flagged this submission for human review.
          </AlertDescription>
        </Alert>

        <!-- Pending Status Alert -->
        <Alert v-else-if="submission.status?.toLowerCase() === 'pending'" class="border-info/40 bg-info/10">
          <Info class="w-4 h-4 text-info" />
          <AlertDescription class="text-info">
            <strong>Pending Approval:</strong> This submission is awaiting manual review before it can be scored.
          </AlertDescription>
        </Alert>

        <!-- Approve/Reject Actions -->
        <Card class="rounded-2xl border-2 border-dashed border-primary/50 bg-primary/5">
          <CardContent class="pt-6">
            <div class="text-center mb-4">
              <h3 class="text-lg font-semibold mb-2">Judge action required</h3>
              <p class="text-sm text-muted-foreground">
                Review the submission details and AI analysis above, then approve or reject this entry.
              </p>
            </div>
            <div class="flex gap-4 justify-center">
              <Button
                variant="brand"
                class="px-8"
                @click="openReviewDialog('approve')"
              >
                <ThumbsUp class="w-4 h-4 mr-2" />
                Approve submission
              </Button>
              <Button
                variant="destructive"
                class="px-8"
                @click="openReviewDialog('reject')"
              >
                <ThumbsDown class="w-4 h-4 mr-2" />
                Reject submission
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Rejected Submission Banner -->
      <Alert v-if="submission.status?.toLowerCase() === 'rejected' && submission.rejection_reason" variant="destructive" class="mb-6">
        <XCircle class="w-4 h-4" />
        <AlertDescription>
          <strong>Rejected:</strong> {{ submission.rejection_reason }}
        </AlertDescription>
      </Alert>

      <!-- Corrective Actions Card - Show when already approved or rejected (allows judges to change decision) -->
      <Card v-if="isApproved || isRejected" class="rounded-2xl mb-6 border-2 border-dashed border-warning/40 bg-warning/5">
        <CardContent class="pt-6">
          <div class="flex items-center justify-between flex-wrap gap-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center"
                   :class="isApproved ? 'bg-success/10' : 'bg-destructive/10'">
                <component :is="isApproved ? CheckCircle : XCircle"
                           :class="isApproved ? 'text-success' : 'text-destructive'"
                           class="w-5 h-5" />
              </div>
              <div>
                <h3 class="text-sm font-semibold">
                  {{ isApproved ? 'Submission Approved' : 'Submission Rejected' }}
                </h3>
                <p class="text-xs text-muted-foreground">
                  {{ isApproved
                    ? 'This submission has been approved and can be scored.'
                    : 'This submission was rejected with the reason shown above.'
                  }}
                </p>
              </div>
            </div>
            <div class="flex gap-3">
              <!-- Show Approve button if currently rejected -->
              <Button
                v-if="isRejected"
                variant="brand"
                @click="openReviewDialog('approve')"
              >
                <ThumbsUp class="w-4 h-4 mr-2" />
                Change to approved
              </Button>
              <!-- Show Reject button if currently approved -->
              <Button
                v-if="isApproved"
                variant="destructive"
                @click="openReviewDialog('reject')"
              >
                <ThumbsDown class="w-4 h-4 mr-2" />
                Change to rejected
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <div class="grid lg:grid-cols-5 gap-4 md:gap-6 lg:gap-8">
        <!-- Left Column: Submission Details (3 cols) -->
        <div class="lg:col-span-3 space-y-4 md:space-y-6">
          <!-- Image & Basic Info Card -->
          <Card class="rounded-2xl">
            <CardHeader>
              <div class="flex items-center justify-between">
                <div>
                  <CardTitle class="text-2xl">{{ submission.title }}</CardTitle>
                  <CardDescription v-if="submission.competition">
                    {{ submission.competition.title }}
                  </CardDescription>
                </div>
                <Badge :variant="submission.status === 'approved' ? 'default' : 'secondary'">
                  {{ submission.status.toUpperCase() }}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <!-- Image preview -->
              <div class="rounded-xl overflow-hidden border bg-muted mb-6 relative group">
                <img
                  v-if="submission.jpg_file_url"
                  :src="getImageUrl(submission.jpg_file_url)"
                  :alt="submission.title"
                  class="w-full h-auto object-contain cursor-zoom-in transition-transform hover:scale-[1.02]"
                  style="max-height: 500px;"
                  @click="openImageLightbox(getImageUrl(submission.jpg_file_url), 'JPG')"
                  @error="(e) => { (e.target as HTMLImageElement).style.display = 'none' }"
                />
                <div v-else class="h-64 flex items-center justify-center">
                  <Camera class="w-12 h-12 text-muted-foreground" />
                </div>
                <!-- View Full Size Button Overlay -->
                <div v-if="submission.jpg_file_url"
                     class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center pointer-events-none">
                  <Button
                    variant="secondary"
                    size="sm"
                    class="opacity-0 group-hover:opacity-100 transition-opacity pointer-events-auto shadow-lg"
                    @click="openImageLightbox(getImageUrl(submission.jpg_file_url), 'JPG')"
                  >
                    <Maximize2 class="w-4 h-4 mr-2" />
                    View full size
                  </Button>
                </div>
              </div>

              <!-- RAW file preview (derived server-side; browsers cannot render RAW) -->
              <div v-if="submission.raw_file_url" class="mb-6">
                <div class="flex items-center gap-3 rounded-2xl border bg-muted/30 p-3">
                  <button
                    v-if="rawPreviewStatus === 'ready' && rawPreviewUrl"
                    type="button"
                    class="relative shrink-0 cursor-zoom-in rounded-lg overflow-hidden border group/raw focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    aria-label="View RAW preview full size"
                    @click="openImageLightbox(rawPreviewUrl, 'RAW preview')"
                  >
                    <img
                      :src="rawPreviewUrl"
                      :alt="`RAW preview of ${submission.title}`"
                      class="h-16 w-24 object-cover transition-transform group-hover/raw:scale-105"
                      @error="rawPreviewStatus = 'unavailable'"
                    />
                    <!-- Where in the RAW the submitted JPG came from, recovered from the
                         geometric homography. Normalised, so percentages work at any size. -->
                    <span
                      v-if="cropRect"
                      class="absolute border-2 border-success shadow-[0_0_0_9999px_rgba(0,0,0,0.45)] pointer-events-none"
                      :style="cropRect"
                    ></span>
                    <span class="absolute inset-0 bg-black/0 group-hover/raw:bg-black/25 transition-colors flex items-center justify-center">
                      <Maximize2 class="w-4 h-4 text-white opacity-0 group-hover/raw:opacity-100 transition-opacity" />
                    </span>
                  </button>
                  <div v-else class="h-16 w-24 shrink-0 rounded-lg border bg-muted flex items-center justify-center">
                    <Loader2 v-if="rawPreviewStatus === 'loading'" class="w-4 h-4 animate-spin text-muted-foreground" />
                    <FileImage v-else class="w-5 h-5 text-muted-foreground" />
                  </div>
                  <div class="min-w-0">
                    <p class="text-sm font-medium flex items-center gap-2">
                      RAW file
                      <Badge v-if="rawExtension" variant="outline" class="text-[10px]">{{ rawExtension }}</Badge>
                    </p>
                    <p class="text-xs text-muted-foreground">
                      {{ rawPreviewStatus === 'ready'
                        ? 'Click the thumbnail to inspect the RAW render'
                        : rawPreviewStatus === 'loading'
                        ? 'Generating preview…'
                        : 'Preview unavailable for this RAW file' }}
                    </p>
                  </div>
                </div>
              </div>

              <p v-if="submission.description" class="text-muted-foreground mb-4">
                {{ submission.description }}
              </p>
            </CardContent>
          </Card>

          <!-- AI Verification Card -->
          <Card class="rounded-2xl overflow-hidden">
            <CardHeader class="border-b">
              <div class="flex items-center gap-3">
                <div class="w-12 h-12 rounded-xl bg-ink text-ink-foreground flex items-center justify-center">
                  <ShieldCheck class="w-6 h-6" />
                </div>
                <div>
                  <CardTitle class="text-xl">AI Verification Analysis</CardTitle>
                  <CardDescription>
                    Automated authenticity verification results
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent class="pt-6">
              <!-- Overall Verdict - Hero Section -->
              <div
                class="relative p-6 rounded-2xl mb-6 overflow-hidden"
                :class="{
                  'bg-success/10 border border-success/30': getPassFailStatus(submission.verification_verdict || '').isPass === true,
                  'bg-destructive/10 border border-destructive/30': getPassFailStatus(submission.verification_verdict || '').isPass === false,
                  'bg-warning/10 border border-warning/30': getPassFailStatus(submission.verification_verdict || '').isPass === null && submission.verification_verdict,
                  'bg-muted/50 border': !submission.verification_verdict
                }"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-4">
                    <div
                      class="w-16 h-16 rounded-2xl flex items-center justify-center"
                      :class="{
                        'bg-success/20': getPassFailStatus(submission.verification_verdict || '').isPass === true,
                        'bg-destructive/20': getPassFailStatus(submission.verification_verdict || '').isPass === false,
                        'bg-warning/20': getPassFailStatus(submission.verification_verdict || '').isPass === null && submission.verification_verdict,
                        'bg-muted': !submission.verification_verdict
                      }"
                    >
                      <component
                        :is="getPassFailStatus(submission.verification_verdict || '').isPass === true ? CheckCircle :
                             getPassFailStatus(submission.verification_verdict || '').isPass === false ? XCircle :
                             ShieldQuestion"
                        class="w-8 h-8"
                        :class="getStatusIconClass(getPassFailStatus(submission.verification_verdict || '').isPass)"
                      />
                    </div>
                    <div>
                      <p class="text-2xl font-display font-semibold tracking-tight">
                        {{ submission.verification_verdict ? submission.verification_verdict.replace('_', ' ').toUpperCase() : 'PENDING ANALYSIS' }}
                      </p>
                      <p class="text-sm text-muted-foreground">Overall Verdict</p>
                    </div>
                  </div>
                  <div class="text-right">
                    <p class="text-4xl font-display font-semibold" :class="getStatusIconClass(getPassFailStatus(submission.verification_verdict || '').isPass)">
                      {{ formatConfidence(submission.verification_confidence) }}
                    </p>
                    <p class="text-sm text-muted-foreground">Confidence</p>
                  </div>
                </div>
              </div>

              <!-- Authenticity Score: the weighted aggregate that decides the verdict -->
              <div v-if="submission.verification_details?.authenticity" class="mb-6">
                <div class="rounded-2xl border-2 overflow-hidden" :class="scoreBandClass(submission.verification_details.authenticity.score)">
                  <div class="p-5">
                    <div class="flex items-start justify-between gap-4 flex-wrap">
                      <div>
                        <p class="text-xs font-bold uppercase tracking-wider text-muted-foreground">Authenticity Score</p>
                        <p class="text-sm font-medium mt-1">{{ submission.verification_details.authenticity.action }}</p>
                        <p class="text-xs text-muted-foreground mt-1">
                          Weighted across {{ submission.verification_details.authenticity.signals.length }} signals
                          ({{ submission.verification_details.authenticity.weight_evaluated }} of 100 points evaluable)
                        </p>
                      </div>
                      <div class="text-right shrink-0">
                        <p class="text-5xl font-display font-semibold leading-none">
                          {{ submission.verification_details.authenticity.score }}<span class="text-2xl text-muted-foreground">/100</span>
                        </p>
                        <p class="text-xs text-muted-foreground mt-1">band {{ submission.verification_details.authenticity.band }}</p>
                      </div>
                    </div>

                    <!-- Band scale -->
                    <div class="mt-4">
                      <div class="h-3 w-full rounded-full bg-muted overflow-hidden flex">
                        <div class="h-full bg-destructive/70" style="width:25%"></div>
                        <div class="h-full bg-warning/70" style="width:25%"></div>
                        <div class="h-full bg-warning/40" style="width:25%"></div>
                        <div class="h-full bg-success/70" style="width:25%"></div>
                      </div>
                      <div class="relative h-4">
                        <div class="absolute -top-1 w-1 h-4 bg-foreground rounded-full"
                             :style="{ left: `calc(${submission.verification_details.authenticity.score}% - 2px)` }"></div>
                      </div>
                      <div class="flex justify-between text-[10px] text-muted-foreground">
                        <span>0 reject</span><span>25</span><span>50 review</span><span>75</span><span>100 approve</span>
                      </div>
                    </div>

                    <!-- Signal breakdown -->
                    <div class="mt-5 space-y-2">
                      <p class="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Evidence by signal</p>
                      <div v-for="signal in submission.verification_details.authenticity.signals" :key="signal.name"
                           class="rounded-xl bg-background/60 border p-3">
                        <div class="flex items-center justify-between gap-3">
                          <span class="text-sm font-medium">{{ signalLabel(signal.name) }}</span>
                          <span class="text-xs text-muted-foreground shrink-0">
                            {{ signal.contribution.toFixed(1) }} / {{ signal.weight }} pts
                          </span>
                        </div>
                        <div class="mt-2 h-1.5 w-full rounded-full bg-muted overflow-hidden">
                          <div class="h-full rounded-full transition-all"
                               :class="signal.score >= 0.75 ? 'bg-success' : signal.score > 0 ? 'bg-warning' : 'bg-destructive'"
                               :style="{ width: `${signal.score * 100}%` }"></div>
                        </div>
                        <p class="text-xs text-muted-foreground mt-2">{{ signal.evidence }}</p>
                      </div>

                      <!-- Signals that could not be measured are excluded, not counted against -->
                      <div v-if="submission.verification_details.authenticity.missing.length"
                           class="rounded-xl bg-muted/40 border border-dashed p-3">
                        <p class="text-xs font-medium">Not evaluable for this submission</p>
                        <p class="text-xs text-muted-foreground mt-1">
                          {{ submission.verification_details.authenticity.missing.map(signalLabel).join(', ') }} —
                          excluded from the score and the remaining weights renormalised, rather than
                          counted against the photographer.
                        </p>
                      </div>
                    </div>

                    <!-- Geometric measurements behind the linkage signal -->
                    <div v-if="submission.verification_details.raw_jpg_linkage?.geometry"
                         class="mt-5 rounded-xl bg-background/60 border p-3">
                      <p class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                        Geometric measurements
                      </p>
                      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                        <div>
                          <p class="text-lg font-display font-semibold">{{ submission.verification_details.raw_jpg_linkage.geometry.inliers }}</p>
                          <p class="text-[10px] text-muted-foreground leading-tight">matching sensor features</p>
                        </div>
                        <div>
                          <p class="text-lg font-display font-semibold">{{ (submission.verification_details.raw_jpg_linkage.geometry.inlier_ratio * 100).toFixed(0) }}%</p>
                          <p class="text-[10px] text-muted-foreground leading-tight">of candidate matches</p>
                        </div>
                        <div>
                          <p class="text-lg font-display font-semibold">{{ ((submission.verification_details.raw_jpg_linkage.crop_fraction ?? 1) * 100).toFixed(0) }}%</p>
                          <p class="text-[10px] text-muted-foreground leading-tight">of the RAW frame used</p>
                        </div>
                        <div>
                          <p class="text-lg font-display font-semibold">{{ submission.verification_details.raw_jpg_linkage.geometry.reproj_error_px.toFixed(2) }}px</p>
                          <p class="text-[10px] text-muted-foreground leading-tight">alignment error</p>
                        </div>
                      </div>
                      <p class="text-xs text-muted-foreground mt-3">
                        {{ submission.verification_details.raw_jpg_linkage.geometry.reason }}
                        <span v-if="cropRect"> The highlighted region on the RAW thumbnail above is where this photograph came from.</span>
                      </p>
                    </div>

                    <!-- Vision arbiter, only present on submissions geometry could not decide -->
                    <div v-if="submission.verification_details.raw_jpg_linkage?.arbitration"
                         class="mt-3 rounded-xl bg-background/60 border p-3">
                      <p class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                        Vision arbiter (consulted only when geometry could not decide)
                      </p>
                      <p class="text-xs text-muted-foreground">
                        {{ submission.verification_details.raw_jpg_linkage.arbitration.reasoning }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Layer Analysis -->
              <div v-if="submission.verification_details" class="space-y-3">
                <div class="flex items-center gap-2 mb-4">
                  <Layers class="w-4 h-4 text-muted-foreground" />
                  <p class="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Layer Analysis</p>
                  <span class="text-xs text-muted-foreground">(Click to expand details)</span>
                </div>

                <!-- Layer 1: Metadata Analysis -->
                <div v-if="submission.verification_details.layer1_result"
                     class="rounded-2xl border-2 transition-all overflow-hidden"
                     :class="getStatusColorClass(getPassFailStatus(submission.verification_details.layer1_result.verdict).isPass)">
                  <!-- Header (clickable) -->
                  <div class="p-4 cursor-pointer hover:bg-muted/30 transition-colors"
                       @click="toggleLayer('layer1')">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl bg-background flex items-center justify-center border">
                          <FileImage class="w-5 h-5 text-foreground" />
                        </div>
                        <div>
                          <div class="flex items-center gap-2">
                            <span class="text-xs font-bold uppercase tracking-wider text-muted-foreground">Layer 1</span>
                          </div>
                          <p class="font-semibold">Metadata Analysis</p>
                          <p class="text-xs text-muted-foreground">EXIF data, camera signatures, AI detection</p>
                        </div>
                      </div>
                      <div class="flex items-center gap-3">
                        <div
                          class="px-4 py-2 rounded-full font-semibold text-sm flex items-center gap-2"
                          :class="{
                            'bg-success text-success-foreground': getPassFailStatus(submission.verification_details.layer1_result.verdict).isPass === true,
                            'bg-destructive text-destructive-foreground': getPassFailStatus(submission.verification_details.layer1_result.verdict).isPass === false,
                            'bg-warning text-warning-foreground': getPassFailStatus(submission.verification_details.layer1_result.verdict).isPass === null
                          }"
                        >
                          <component
                            :is="getPassFailStatus(submission.verification_details.layer1_result.verdict).isPass === true ? CheckCircle :
                                 getPassFailStatus(submission.verification_details.layer1_result.verdict).isPass === false ? XCircle :
                                 AlertTriangle"
                            class="w-4 h-4"
                          />
                          {{ getPassFailStatus(submission.verification_details.layer1_result.verdict).status }}
                        </div>
                        <component :is="expandedLayers.layer1 ? ChevronUp : ChevronDown" class="w-5 h-5 text-muted-foreground" />
                      </div>
                    </div>
                  </div>
                  <!-- Expanded Details -->
                  <div v-if="expandedLayers.layer1" class="px-4 pb-4 pt-2 border-t bg-background/50 space-y-4">
                    <!-- Analysis Metrics -->
                    <div class="grid grid-cols-2 gap-4">
                      <div class="p-3 rounded-lg bg-muted/30">
                        <div class="flex items-center gap-2 mb-2">
                          <Camera class="w-4 h-4 text-muted-foreground" />
                          <span class="text-sm font-medium">Camera Fields</span>
                        </div>
                        <p class="text-2xl font-display font-semibold">{{ submission.verification_details.layer1_result.camera_fields_found ?? 0 }}/8</p>
                        <div class="mt-2 h-2 bg-muted rounded-full overflow-hidden">
                          <div class="h-full transition-all duration-500"
                               :class="getScoreBarColor((submission.verification_details.layer1_result.camera_fields_found ?? 0) / 8)"
                               :style="{ width: `${((submission.verification_details.layer1_result.camera_fields_found ?? 0) / 8) * 100}%` }"></div>
                        </div>
                        <p class="text-xs text-muted-foreground mt-1">Make, Model, Lens, ISO, Aperture, Shutter, Focal, Date</p>
                      </div>
                      <div class="p-3 rounded-lg bg-muted/30">
                        <div class="flex items-center gap-2 mb-2">
                          <Cpu class="w-4 h-4 text-muted-foreground" />
                          <span class="text-sm font-medium">AI Signatures</span>
                        </div>
                        <p class="text-2xl font-display font-semibold" :class="(submission.verification_details.layer1_result.ai_signatures_found ?? 0) > 0 ? 'text-destructive' : 'text-success'">
                          {{ submission.verification_details.layer1_result.ai_signatures_found ?? 0 }}
                        </p>
                        <p class="text-xs text-muted-foreground mt-1">Midjourney, DALL-E, Stable Diffusion, etc.</p>
                      </div>
                    </div>
                    <!-- Score Breakdown -->
                    <div class="space-y-3">
                      <p class="text-sm font-semibold">Score Breakdown</p>
                      <div class="space-y-2">
                        <div class="flex items-center justify-between">
                          <span class="text-sm text-muted-foreground">Camera Score (40%)</span>
                          <div class="flex items-center gap-2">
                            <div class="w-24 h-2 bg-muted rounded-full overflow-hidden">
                              <div class="h-full transition-all duration-500"
                                   :class="getScoreBarColor(submission.verification_details.layer1_result.camera_score ?? 0)"
                                   :style="{ width: `${(submission.verification_details.layer1_result.camera_score ?? 0) * 100}%` }"></div>
                            </div>
                            <span class="text-sm font-medium w-12 text-right">{{ formatScore(submission.verification_details.layer1_result.camera_score) }}</span>
                          </div>
                        </div>
                        <div class="flex items-center justify-between">
                          <span class="text-sm text-muted-foreground">Consistency Score (60%)</span>
                          <div class="flex items-center gap-2">
                            <div class="w-24 h-2 bg-muted rounded-full overflow-hidden">
                              <div class="h-full transition-all duration-500"
                                   :class="getScoreBarColor(submission.verification_details.layer1_result.consistency_score ?? 0)"
                                   :style="{ width: `${(submission.verification_details.layer1_result.consistency_score ?? 0) * 100}%` }"></div>
                            </div>
                            <span class="text-sm font-medium w-12 text-right">{{ formatScore(submission.verification_details.layer1_result.consistency_score) }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <!-- Flags -->
                    <div v-if="submission.verification_details.layer1_result.flags?.length" class="space-y-2">
                      <p class="text-sm font-semibold flex items-center gap-2">
                        <Info class="w-4 h-4" />
                        Detection Notes
                      </p>
                      <ul class="space-y-1">
                        <li v-for="(flag, idx) in submission.verification_details.layer1_result.flags" :key="idx"
                            class="text-xs text-muted-foreground flex items-start gap-2 p-2 rounded bg-muted/30">
                          <span class="text-info mt-0.5">•</span>
                          {{ flag }}
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>

                <!-- Layer 2: Fingerprint Analysis -->
                <div v-if="submission.verification_details.layer2_result"
                     class="rounded-2xl border-2 transition-all overflow-hidden"
                     :class="getStatusColorClass(getPassFailStatus(submission.verification_details.layer2_result.verdict).isPass)">
                  <!-- Header (clickable) -->
                  <div class="p-4 cursor-pointer hover:bg-muted/30 transition-colors"
                       @click="toggleLayer('layer2')">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl bg-background flex items-center justify-center border">
                          <Fingerprint class="w-5 h-5 text-foreground" />
                        </div>
                        <div>
                          <div class="flex items-center gap-2">
                            <span class="text-xs font-bold uppercase tracking-wider text-muted-foreground">Layer 2</span>
                          </div>
                          <p class="font-semibold">Digital Fingerprint Analysis</p>
                          <p class="text-xs text-muted-foreground">PRNU, ELA, FFT forensic analysis</p>
                        </div>
                      </div>
                      <div class="flex items-center gap-3">
                        <span class="text-lg font-bold" :class="getStatusIconClass(getPassFailStatus(submission.verification_details.layer2_result.verdict).isPass)">
                          {{ formatConfidence(submission.verification_details.layer2_result.confidence) }}
                        </span>
                        <div
                          class="px-4 py-2 rounded-full font-semibold text-sm flex items-center gap-2"
                          :class="{
                            'bg-success text-success-foreground': getPassFailStatus(submission.verification_details.layer2_result.verdict).isPass === true,
                            'bg-destructive text-destructive-foreground': getPassFailStatus(submission.verification_details.layer2_result.verdict).isPass === false,
                            'bg-warning text-warning-foreground': getPassFailStatus(submission.verification_details.layer2_result.verdict).isPass === null
                          }"
                        >
                          <component
                            :is="getPassFailStatus(submission.verification_details.layer2_result.verdict).isPass === true ? CheckCircle :
                                 getPassFailStatus(submission.verification_details.layer2_result.verdict).isPass === false ? XCircle :
                                 AlertTriangle"
                            class="w-4 h-4"
                          />
                          {{ getPassFailStatus(submission.verification_details.layer2_result.verdict).status }}
                        </div>
                        <component :is="expandedLayers.layer2 ? ChevronUp : ChevronDown" class="w-5 h-5 text-muted-foreground" />
                      </div>
                    </div>
                  </div>
                  <!-- Expanded Details -->
                  <div v-if="expandedLayers.layer2" class="px-4 pb-4 pt-2 border-t bg-background/50 space-y-4">
                    <!-- Three Analysis Methods -->
                    <div class="grid grid-cols-3 gap-3">
                      <div class="p-3 rounded-lg bg-muted/30 text-center">
                        <div class="w-10 h-10 rounded-full bg-secondary flex items-center justify-center mx-auto mb-2">
                          <Waves class="w-5 h-5 text-foreground" />
                        </div>
                        <p class="text-xs font-bold uppercase text-muted-foreground mb-1">PRNU</p>
                        <p class="text-xl font-display font-semibold" :class="getStatusIconClass((submission.verification_details.layer2_result.prnu_score ?? 0) >= 0.5)">
                          {{ formatScore(submission.verification_details.layer2_result.prnu_score) }}
                        </p>
                        <p class="text-xs text-muted-foreground mt-1">Sensor Noise Pattern</p>
                      </div>
                      <div class="p-3 rounded-lg bg-muted/30 text-center">
                        <div class="w-10 h-10 rounded-full bg-secondary flex items-center justify-center mx-auto mb-2">
                          <Grid3X3 class="w-5 h-5 text-foreground" />
                        </div>
                        <p class="text-xs font-bold uppercase text-muted-foreground mb-1">ELA</p>
                        <p class="text-xl font-display font-semibold" :class="getStatusIconClass((submission.verification_details.layer2_result.ela_score ?? 0) >= 0.5)">
                          {{ formatScore(submission.verification_details.layer2_result.ela_score) }}
                        </p>
                        <p class="text-xs text-muted-foreground mt-1">Compression Artifacts</p>
                      </div>
                      <div class="p-3 rounded-lg bg-muted/30 text-center">
                        <div class="w-10 h-10 rounded-full bg-secondary flex items-center justify-center mx-auto mb-2">
                          <BarChart2 class="w-5 h-5 text-foreground" />
                        </div>
                        <p class="text-xs font-bold uppercase text-muted-foreground mb-1">FFT</p>
                        <p class="text-xl font-display font-semibold" :class="getStatusIconClass((submission.verification_details.layer2_result.fft_score ?? 0) >= 0.5)">
                          {{ formatScore(submission.verification_details.layer2_result.fft_score) }}
                        </p>
                        <p class="text-xs text-muted-foreground mt-1">Frequency Analysis</p>
                      </div>
                    </div>
                    <!-- Technical Metrics -->
                    <div class="p-3 rounded-lg bg-muted/20 space-y-2">
                      <p class="text-sm font-semibold">Technical Metrics</p>
                      <div class="grid grid-cols-3 gap-4 text-center text-xs">
                        <div>
                          <p class="text-muted-foreground">PRNU Energy</p>
                          <p class="font-mono font-bold">{{ submission.verification_details.layer2_result.prnu_energy?.toFixed(6) ?? 'N/A' }}</p>
                        </div>
                        <div>
                          <p class="text-muted-foreground">ELA Uniformity</p>
                          <p class="font-mono font-bold">{{ submission.verification_details.layer2_result.ela_uniformity?.toFixed(2) ?? 'N/A' }}</p>
                        </div>
                        <div>
                          <p class="text-muted-foreground">High-Freq Ratio</p>
                          <p class="font-mono font-bold">{{ submission.verification_details.layer2_result.fft_high_freq_ratio?.toFixed(4) ?? 'N/A' }}</p>
                        </div>
                      </div>
                    </div>
                    <!-- Weight Explanation -->
                    <div class="p-3 rounded-lg bg-info/10 border border-info/20">
                      <p class="text-xs text-info flex items-center gap-2">
                        <Info class="w-4 h-4" />
                        <span><strong>Scoring:</strong> PRNU (50%) + ELA (25%) + FFT (25%) = Final Score</span>
                      </p>
                    </div>
                    <!-- Flags -->
                    <div v-if="submission.verification_details.layer2_result.flags?.length" class="space-y-2">
                      <p class="text-sm font-semibold flex items-center gap-2">
                        <Info class="w-4 h-4" />
                        Detection Notes
                      </p>
                      <ul class="space-y-1">
                        <li v-for="(flag, idx) in submission.verification_details.layer2_result.flags" :key="idx"
                            class="text-xs text-muted-foreground flex items-start gap-2 p-2 rounded bg-muted/30">
                          <span class="text-info mt-0.5">•</span>
                          {{ flag }}
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>

                <!-- Layer 3: Third-Party API Verification -->
                <div v-if="submission.verification_details.layer3_result"
                     class="rounded-2xl border-2 transition-all overflow-hidden"
                     :class="getStatusColorClass(getPassFailStatus(submission.verification_details.layer3_result.verdict).isPass)">
                  <!-- Header (clickable) -->
                  <div class="p-4 cursor-pointer hover:bg-muted/30 transition-colors"
                       @click="toggleLayer('layer3')">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl bg-background flex items-center justify-center border">
                          <Globe class="w-5 h-5 text-foreground" />
                        </div>
                        <div>
                          <div class="flex items-center gap-2">
                            <span class="text-xs font-bold uppercase tracking-wider text-muted-foreground">Layer 3</span>
                          </div>
                          <p class="font-semibold">Third-Party API Verification</p>
                          <p class="text-xs text-muted-foreground">External AI detection services</p>
                        </div>
                      </div>
                      <div class="flex items-center gap-3">
                        <span class="text-lg font-bold" :class="getStatusIconClass(getPassFailStatus(submission.verification_details.layer3_result.verdict).isPass)">
                          {{ formatConfidence(submission.verification_details.layer3_result.confidence) }}
                        </span>
                        <div
                          class="px-4 py-2 rounded-full font-semibold text-sm flex items-center gap-2"
                          :class="{
                            'bg-success text-success-foreground': getPassFailStatus(submission.verification_details.layer3_result.verdict).isPass === true,
                            'bg-destructive text-destructive-foreground': getPassFailStatus(submission.verification_details.layer3_result.verdict).isPass === false,
                            'bg-warning text-warning-foreground': getPassFailStatus(submission.verification_details.layer3_result.verdict).isPass === null
                          }"
                        >
                          <component
                            :is="getPassFailStatus(submission.verification_details.layer3_result.verdict).isPass === true ? CheckCircle :
                                 getPassFailStatus(submission.verification_details.layer3_result.verdict).isPass === false ? XCircle :
                                 AlertTriangle"
                            class="w-4 h-4"
                          />
                          {{ getPassFailStatus(submission.verification_details.layer3_result.verdict).status }}
                        </div>
                        <component :is="expandedLayers.layer3 ? ChevronUp : ChevronDown" class="w-5 h-5 text-muted-foreground" />
                      </div>
                    </div>
                  </div>
                  <!-- Expanded Details -->
                  <div v-if="expandedLayers.layer3" class="px-4 pb-4 pt-2 border-t bg-background/50 space-y-4">
                    <div class="p-4 rounded-lg bg-muted/20 text-center">
                      <p class="text-sm text-muted-foreground mb-2">External API Confidence</p>
                      <p class="text-4xl font-display font-semibold" :class="getStatusIconClass(getPassFailStatus(submission.verification_details.layer3_result.verdict).isPass)">
                        {{ formatConfidence(submission.verification_details.layer3_result.confidence) }}
                      </p>
                    </div>
                    <div class="p-3 rounded-lg bg-info/10 border border-info/20">
                      <p class="text-xs text-info flex items-center gap-2">
                        <Info class="w-4 h-4" />
                        <span>Layer 3 runs only when Layer 2 returns SUSPICIOUS verdict</span>
                      </p>
                    </div>
                    <!-- Flags -->
                    <div v-if="submission.verification_details.layer3_result.flags?.length" class="space-y-2">
                      <p class="text-sm font-semibold flex items-center gap-2">
                        <Info class="w-4 h-4" />
                        API Response
                      </p>
                      <ul class="space-y-1">
                        <li v-for="(flag, idx) in submission.verification_details.layer3_result.flags" :key="idx"
                            class="text-xs text-muted-foreground flex items-start gap-2 p-2 rounded bg-muted/30">
                          <span class="text-info mt-0.5">•</span>
                          {{ flag }}
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>

                <!-- RAW-JPG Linkage Analysis -->
                <div v-if="submission.verification_details.raw_jpg_linkage"
                     class="rounded-2xl border-2 transition-all overflow-hidden"
                     :class="getStatusColorClass(getPassFailStatus(submission.verification_details.raw_jpg_linkage.verdict).isPass)">
                  <!-- Header (clickable) -->
                  <div class="p-4 cursor-pointer hover:bg-muted/30 transition-colors"
                       @click="toggleLayer('rawLinkage')">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl bg-background flex items-center justify-center border">
                          <Link class="w-5 h-5 text-foreground" />
                        </div>
                        <div>
                          <div class="flex items-center gap-2">
                            <span class="text-xs font-bold uppercase tracking-wider text-muted-foreground">RAW Linkage</span>
                          </div>
                          <p class="font-semibold">RAW-JPG File Linkage</p>
                          <p class="text-xs text-muted-foreground">pHash, SSIM, Histogram verification</p>
                        </div>
                      </div>
                      <div class="flex items-center gap-3">
                        <span v-if="submission.verification_details.raw_jpg_linkage.confidence"
                              class="text-lg font-bold"
                              :class="getStatusIconClass(getPassFailStatus(submission.verification_details.raw_jpg_linkage.verdict).isPass)">
                          {{ formatConfidence(submission.verification_details.raw_jpg_linkage.confidence) }}
                        </span>
                        <div
                          class="px-4 py-2 rounded-full font-semibold text-sm flex items-center gap-2"
                          :class="{
                            'bg-success text-success-foreground': getPassFailStatus(submission.verification_details.raw_jpg_linkage.verdict).isPass === true,
                            'bg-destructive text-destructive-foreground': getPassFailStatus(submission.verification_details.raw_jpg_linkage.verdict).isPass === false,
                            'bg-warning text-warning-foreground': getPassFailStatus(submission.verification_details.raw_jpg_linkage.verdict).isPass === null
                          }"
                        >
                          <component
                            :is="getPassFailStatus(submission.verification_details.raw_jpg_linkage.verdict).isPass === true ? CheckCircle :
                                 getPassFailStatus(submission.verification_details.raw_jpg_linkage.verdict).isPass === false ? XCircle :
                                 AlertTriangle"
                            class="w-4 h-4"
                          />
                          {{ getPassFailStatus(submission.verification_details.raw_jpg_linkage.verdict).status }}
                        </div>
                        <component :is="expandedLayers.rawLinkage ? ChevronUp : ChevronDown" class="w-5 h-5 text-muted-foreground" />
                      </div>
                    </div>
                  </div>
                  <!-- Expanded Details -->
                  <div v-if="expandedLayers.rawLinkage" class="px-4 pb-4 pt-2 border-t bg-background/50 space-y-4">
                    <!-- Three Comparison Methods -->
                    <div class="grid grid-cols-3 gap-3">
                      <div class="p-3 rounded-lg bg-muted/30 text-center">
                        <div class="w-10 h-10 rounded-full bg-secondary flex items-center justify-center mx-auto mb-2">
                          <Hash class="w-5 h-5 text-foreground" />
                        </div>
                        <p class="text-xs font-bold uppercase text-muted-foreground mb-1">pHash</p>
                        <p class="text-xl font-display font-semibold">{{ submission.verification_details.raw_jpg_linkage.phash_distance ?? 'N/A' }}</p>
                        <p class="text-xs text-muted-foreground mt-1">Hamming Distance</p>
                        <p class="text-xs" :class="(submission.verification_details.raw_jpg_linkage.phash_distance ?? 999) <= 15 ? 'text-success' : 'text-destructive'">
                          {{ (submission.verification_details.raw_jpg_linkage.phash_distance ?? 999) <= 15 ? '≤15 PASS' : '>15 FAIL' }}
                        </p>
                      </div>
                      <div class="p-3 rounded-lg bg-muted/30 text-center">
                        <div class="w-10 h-10 rounded-full bg-secondary flex items-center justify-center mx-auto mb-2">
                          <ImageIcon class="w-5 h-5 text-foreground" />
                        </div>
                        <p class="text-xs font-bold uppercase text-muted-foreground mb-1">SSIM</p>
                        <p class="text-xl font-display font-semibold" :class="getStatusIconClass((submission.verification_details.raw_jpg_linkage.ssim_score ?? 0) >= 0.45)">
                          {{ submission.verification_details.raw_jpg_linkage.ssim_score?.toFixed(2) ?? 'N/A' }}
                        </p>
                        <p class="text-xs text-muted-foreground mt-1">Structural Similarity</p>
                        <p class="text-xs" :class="(submission.verification_details.raw_jpg_linkage.ssim_score ?? 0) >= 0.45 ? 'text-success' : 'text-destructive'">
                          {{ (submission.verification_details.raw_jpg_linkage.ssim_score ?? 0) >= 0.45 ? '≥0.45 PASS' : '<0.45 FAIL' }}
                        </p>
                      </div>
                      <div class="p-3 rounded-lg bg-muted/30 text-center">
                        <div class="w-10 h-10 rounded-full bg-secondary flex items-center justify-center mx-auto mb-2">
                          <BarChart2 class="w-5 h-5 text-foreground" />
                        </div>
                        <p class="text-xs font-bold uppercase text-muted-foreground mb-1">Histogram</p>
                        <p class="text-xl font-display font-semibold" :class="getStatusIconClass((submission.verification_details.raw_jpg_linkage.histogram_correlation ?? 0) >= 0.40)">
                          {{ submission.verification_details.raw_jpg_linkage.histogram_correlation?.toFixed(2) ?? 'N/A' }}
                        </p>
                        <p class="text-xs text-muted-foreground mt-1">Color Correlation</p>
                        <p class="text-xs" :class="(submission.verification_details.raw_jpg_linkage.histogram_correlation ?? 0) >= 0.40 ? 'text-success' : 'text-destructive'">
                          {{ (submission.verification_details.raw_jpg_linkage.histogram_correlation ?? 0) >= 0.40 ? '≥0.40 PASS' : '<0.40 FAIL' }}
                        </p>
                      </div>
                    </div>
                    <!-- Explanation -->
                    <div class="p-3 rounded-lg bg-info/10 border border-info/20">
                      <p class="text-xs text-info flex items-center gap-2">
                        <Info class="w-4 h-4" />
                        <span><strong>Verdict:</strong> 3 methods pass = Strong Link | 2 methods = Probable Link | 1 method = Suspicious | 0 methods = Reject</span>
                      </p>
                    </div>
                    <!-- Flags -->
                    <div v-if="submission.verification_details.raw_jpg_linkage.flags?.length" class="space-y-2">
                      <p class="text-sm font-semibold flex items-center gap-2">
                        <Info class="w-4 h-4" />
                        Analysis Details
                      </p>
                      <ul class="space-y-1">
                        <li v-for="(flag, idx) in submission.verification_details.raw_jpg_linkage.flags" :key="idx"
                            class="text-xs text-muted-foreground flex items-start gap-2 p-2 rounded bg-muted/30">
                          <span class="text-info mt-0.5">•</span>
                          {{ flag }}
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>

                <!-- Detection Flags -->
                <div v-if="submission.verification_details.flags && submission.verification_details.flags.length > 0"
                     class="mt-4 p-4 rounded-xl bg-warning/10 border border-warning/20">
                  <div class="flex items-center gap-2 mb-2">
                    <AlertTriangle class="w-4 h-4 text-warning" />
                    <span class="text-sm font-semibold text-warning">Detection Flags</span>
                  </div>
                  <ul class="space-y-1">
                    <li v-for="(flag, idx) in submission.verification_details.flags"
                        :key="idx"
                        class="text-sm text-muted-foreground flex items-start gap-2">
                      <span class="text-warning mt-1">•</span>
                      {{ flag }}
                    </li>
                  </ul>
                </div>

                <!-- Processing Time -->
                <div v-if="submission.verification_details.processing_time_ms"
                     class="mt-4 pt-4 border-t flex items-center justify-between text-sm text-muted-foreground">
                  <span>Analysis completed</span>
                  <span>{{ (submission.verification_details.processing_time_ms / 1000).toFixed(2) }}s processing time</span>
                </div>
              </div>

              <!-- No analysis yet -->
              <div v-else class="text-center py-8 text-muted-foreground">
                <div class="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mx-auto mb-4">
                  <Loader2 class="w-8 h-8 animate-spin" />
                </div>
                <p class="font-medium">AI Analysis Pending</p>
                <p class="text-sm">Verification results will appear here once complete</p>
              </div>
            </CardContent>
          </Card>

          <!-- Camera Info Card -->
          <Card class="rounded-2xl">
            <CardHeader>
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
                  <Camera class="w-5 h-5 text-foreground" />
                </div>
                <CardTitle class="text-lg">Camera & Settings</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div v-if="cameraDisplayName" class="p-3 rounded-lg bg-muted/50">
                  <p class="text-xs text-muted-foreground mb-1">Camera</p>
                  <p class="font-medium text-sm">{{ cameraDisplayName }}</p>
                </div>
                <div v-if="submission.lens_model" class="p-3 rounded-lg bg-muted/50">
                  <p class="text-xs text-muted-foreground mb-1">Lens</p>
                  <p class="font-medium text-sm">{{ submission.lens_model }}</p>
                </div>
                <div v-if="submission.iso" class="p-3 rounded-lg bg-muted/50">
                  <p class="text-xs text-muted-foreground mb-1">ISO</p>
                  <p class="font-medium text-sm">{{ submission.iso }}</p>
                </div>
                <div v-if="submission.aperture" class="p-3 rounded-lg bg-muted/50">
                  <p class="text-xs text-muted-foreground mb-1">Aperture</p>
                  <p class="font-medium text-sm">{{ submission.aperture }}</p>
                </div>
                <div v-if="submission.shutter_speed" class="p-3 rounded-lg bg-muted/50">
                  <p class="text-xs text-muted-foreground mb-1">Shutter Speed</p>
                  <p class="font-medium text-sm">{{ submission.shutter_speed }}</p>
                </div>
                <div v-if="submission.capture_date" class="p-3 rounded-lg bg-muted/50">
                  <p class="text-xs text-muted-foreground mb-1">Capture Date</p>
                  <p class="font-medium text-sm">{{ submission.capture_date }}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- V2.0: Camera Reputation Card (for judges/admins) -->
          <CameraReputationCard
            v-if="submission.camera_make && submission.camera_model"
            :submission-id="submission.id"
            :camera-make="submission.camera_make"
            :camera-model="submission.camera_model"
            :trust-score="submission.camera_trust_score"
            :prnu-energy="submission.prnu_extracted_energy"
            :verified="submission.prnu_fingerprint_id != null"
            class="mt-4"
          />

          <!-- V2.0: Consensus Indicator - Only show when there are scores from multiple judges -->
          <ConsensusIndicator
            v-if="submission.score_count >= 2"
            :judge-count="submission.score_count"
            size="md"
            class="mt-4"
          />
        </div>

        <!-- Right Column: Scoring Form (2 cols) -->
        <div class="lg:col-span-2">
          <Card class="rounded-2xl lg:sticky lg:top-6">
            <CardHeader>
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
                  <Star class="w-5 h-5 text-foreground" />
                </div>
                <div>
                  <CardTitle>{{ alreadyScored ? 'Update score' : 'Score this submission' }}</CardTitle>
                  <CardDescription>
                    {{ canBeScored ? 'Rate each category from 0 to 10' : 'Submission must be approved before scoring' }}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <!-- Not approved message -->
              <div v-if="!canBeScored && !alreadyScored" class="text-center py-8">
                <div class="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mx-auto mb-4">
                  <AlertCircle class="w-8 h-8 text-muted-foreground" />
                </div>
                <p class="font-medium text-muted-foreground mb-2">Cannot Score Yet</p>
                <p class="text-sm text-muted-foreground">
                  {{ submission.status?.toLowerCase() === 'pending' || submission.analysis_error
                    ? 'Please approve or reject this submission using the buttons above.'
                    : submission.status?.toLowerCase() === 'rejected'
                    ? 'This submission has been rejected and cannot be scored.'
                    : 'This submission is not ready for scoring.' }}
                </p>
              </div>
              <!-- Scoring form (only shown when can be scored) -->
              <div v-if="canBeScored || alreadyScored">
                <Alert v-if="error" variant="destructive" class="mb-4">
                  <AlertDescription>{{ error }}</AlertDescription>
                </Alert>

                <Alert v-if="success" class="mb-4 bg-success/10 text-success border-success/30">
                  <AlertDescription>{{ success }}</AlertDescription>
                </Alert>

                <form @submit.prevent="handleSubmit" class="space-y-5">
                <!-- Score Categories -->
                <div
                  v-for="category in scoreCategories"
                  :key="category.id"
                  class="p-4 rounded-xl bg-muted/30 border space-y-3"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                        <component :is="category.icon" class="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <Label :for="category.id" class="text-sm font-medium">{{ category.label }}</Label>
                        <span class="text-xs text-muted-foreground ml-1">({{ category.weight }})</span>
                      </div>
                    </div>
                    <span class="text-2xl font-display font-semibold text-primary">{{ category.model.value }}</span>
                  </div>
                  <input
                    :id="category.id"
                    type="range"
                    min="0"
                    max="10"
                    step="0.5"
                    v-model.number="category.model.value"
                    class="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                    :disabled="isSubmitting"
                  />
                  <p class="text-xs text-muted-foreground">
                    {{ category.description }}
                  </p>
                </div>

                <!-- Overall Score Preview -->
                <div class="p-5 rounded-2xl bg-ink text-ink-foreground text-center">
                  <p class="text-sm text-ink-muted mb-1">Overall Score</p>
                  <p class="text-4xl font-display font-semibold text-brand">{{ overallScorePreview }}</p>
                </div>

                <!-- Judge Identifier (for shared credentials tracking) -->
                <div class="space-y-2">
                  <Label for="judgeIdentifier">Your Name/Identifier (Optional)</Label>
                  <Input
                    id="judgeIdentifier"
                    v-model="judgeIdentifier"
                    placeholder="Enter your display name"
                    :disabled="isSubmitting"
                    maxlength="100"
                  />
                  <p class="text-xs text-muted-foreground">
                    Optional display name recorded with this score.
                  </p>
                </div>

                <!-- Comments -->
                <div class="space-y-2">
                  <Label for="comments">Comments (Optional)</Label>
                  <Textarea
                    id="comments"
                    v-model="comments"
                    placeholder="Provide feedback for the photographer..."
                    rows="3"
                    :disabled="isSubmitting"
                  />
                </div>

                <!-- Submit button -->
                <div class="flex gap-3 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    @click="router.back()"
                    :disabled="isSubmitting"
                    class="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button type="submit" class="flex-1" :disabled="isSubmitting">
                    <Loader2 v-if="isSubmitting" class="w-4 h-4 mr-2 animate-spin" />
                    {{ isSubmitting ? 'Submitting...' : (alreadyScored ? 'Update score' : 'Submit score') }}
                  </Button>
                </div>
              </form>
              </div>
            </CardContent>
          </Card>
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
              ? 'This will approve the submission for scoring by all judges.'
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

    <!-- Image Lightbox Modal -->
    <Teleport to="body">
      <Transition name="lightbox">
        <div
          v-if="showImageLightbox && lightboxSrc && submission"
          class="fixed inset-0 z-50 bg-black/95 flex flex-col"
          @wheel.prevent="handleWheel"
          @mouseup="handleMouseUp"
          @mouseleave="handleMouseUp"
        >
          <!-- Lightbox Header -->
          <div class="flex items-center justify-between p-4 bg-black/50">
            <div class="text-white">
              <h3 class="font-semibold">{{ submission.title }}</h3>
              <p class="text-sm text-ink-muted">
                {{ cameraDisplayName }}<span v-if="lightboxLabel"> · {{ lightboxLabel }}</span>
              </p>
            </div>
            <div class="flex items-center gap-2">
              <!-- Zoom Controls -->
              <div class="flex items-center gap-1 bg-white/10 rounded-lg p-1">
                <Button variant="ghost" size="icon" class="h-8 w-8 text-white hover:bg-white/20" aria-label="Zoom out" @click="zoomOut">
                  <ZoomOut class="w-4 h-4" />
                </Button>
                <span class="text-white text-sm font-mono w-14 text-center">{{ (imageZoom * 100).toFixed(0) }}%</span>
                <Button variant="ghost" size="icon" class="h-8 w-8 text-white hover:bg-white/20" aria-label="Zoom in" @click="zoomIn">
                  <ZoomIn class="w-4 h-4" />
                </Button>
              </div>
              <!-- Reset Zoom -->
              <Button variant="ghost" size="icon" class="h-8 w-8 text-white hover:bg-white/20" aria-label="Reset zoom" @click="resetZoom" title="Reset zoom (0)">
                <Maximize2 class="w-4 h-4" />
              </Button>
              <!-- Rotate -->
              <Button variant="ghost" size="icon" class="h-8 w-8 text-white hover:bg-white/20" aria-label="Rotate" @click="rotateImage" title="Rotate (R)">
                <RotateCw class="w-4 h-4" />
              </Button>
              <!-- Close -->
              <Button variant="ghost" size="icon" class="h-8 w-8 text-white hover:bg-white/20" aria-label="Close" @click="closeImageLightbox">
                <X class="w-5 h-5" />
              </Button>
            </div>
          </div>

          <!-- Image Container -->
          <div
            class="flex-1 overflow-hidden flex items-center justify-center cursor-grab"
            :class="{ 'cursor-grabbing': isDragging }"
            @mousedown="handleMouseDown"
            @mousemove="handleMouseMove"
          >
            <img
              :src="lightboxSrc"
              :alt="`${submission.title} — ${lightboxLabel}`"
              class="max-w-none select-none transition-transform duration-150"
              :style="{
                transform: `translate(${imagePosition.x}px, ${imagePosition.y}px) scale(${imageZoom}) rotate(${imageRotation}deg)`,
                maxHeight: imageZoom === 1 ? '90vh' : 'none',
                maxWidth: imageZoom === 1 ? '95vw' : 'none'
              }"
              draggable="false"
            />
          </div>

          <!-- Lightbox Footer - Keyboard Shortcuts -->
          <div class="p-3 bg-black/50 text-center">
            <p class="text-xs text-ink-muted">
              <kbd class="px-1.5 py-0.5 bg-white/10 rounded text-white">+</kbd> / <kbd class="px-1.5 py-0.5 bg-white/10 rounded text-white">-</kbd> Zoom
              <span class="mx-2">|</span>
              <kbd class="px-1.5 py-0.5 bg-white/10 rounded text-white">0</kbd> Reset
              <span class="mx-2">|</span>
              <kbd class="px-1.5 py-0.5 bg-white/10 rounded text-white">R</kbd> Rotate
              <span class="mx-2">|</span>
              <kbd class="px-1.5 py-0.5 bg-white/10 rounded text-white">Esc</kbd> Close
              <span class="mx-2">|</span>
              <span class="text-ink-muted">Scroll to zoom • Drag to pan when zoomed</span>
            </p>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
/* Lightbox transition animations */
.lightbox-enter-active,
.lightbox-leave-active {
  transition: opacity 0.3s ease;
}

.lightbox-enter-from,
.lightbox-leave-to {
  opacity: 0;
}

.lightbox-enter-active img,
.lightbox-leave-active img {
  transition: transform 0.3s ease;
}

.lightbox-enter-from img {
  transform: scale(0.9);
}

.lightbox-leave-to img {
  transform: scale(0.9);
}
</style>
