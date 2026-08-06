<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useSubmissionsStore } from '@/stores/submissions'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Camera, Clock, ImageIcon, Trophy, Search, X, AlertCircle, XCircle, Info, CheckCircle, Gavel, Loader2 } from 'lucide-vue-next'
import type { Submission } from '@/types'

const authStore = useAuthStore()
const submissionsStore = useSubmissionsStore()
const loadError = ref('')
const searchQuery = ref('')
const statusFilter = ref<string>('all')
const selectedSubmission = ref<Submission | null>(null)
const isModalOpen = ref(false)
let pollingInterval: ReturnType<typeof setInterval> | null = null

const statusOptions = [
  { value: 'all', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'analyzing', label: 'Analyzing' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'disqualified', label: 'Disqualified' },
]

const filteredSubmissions = computed(() => {
  let submissions = submissionsStore.submissions

  // Filter by search query
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    submissions = submissions.filter(s =>
      s.title.toLowerCase().includes(query) ||
      s.description?.toLowerCase().includes(query) ||
      s.competition?.title.toLowerCase().includes(query)
    )
  }

  // Filter by status
  if (statusFilter.value !== 'all') {
    submissions = submissions.filter(s => s.status === statusFilter.value)
  }

  return submissions
})

const loadSubmissions = async () => {
  try {
    loadError.value = ''
    if (authStore.user) {
      await submissionsStore.fetchSubmissions({ user_id: authStore.user.id })
    }
  } catch (error: unknown) {
    if (error instanceof Error) {
      loadError.value = error.message || 'Failed to load submissions'
    } else {
      loadError.value = 'Failed to load submissions. Please try again.'
    }
  }
}

const hasAnalyzingSubmission = computed(() => {
  return submissionsStore.submissions.some(s => s.status === 'analyzing')
})

const startPolling = () => {
  if (pollingInterval) return
  pollingInterval = setInterval(async () => {
    if (hasAnalyzingSubmission.value) {
      await loadSubmissions()
    } else {
      stopPolling()
    }
  }, 3000)
}

const stopPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
}

onMounted(() => {
  loadSubmissions().then(() => {
    if (hasAnalyzingSubmission.value) {
      startPolling()
    }
  })
})

onUnmounted(() => {
  stopPolling()
})

const openModal = (submission: Submission) => {
  selectedSubmission.value = submission
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
  selectedSubmission.value = null
}

const getStatusVariant = (status: string) => {
  const variants: Record<string, string> = {
    pending: 'secondary',
    analyzing: 'secondary',
    approved: 'default',
    rejected: 'destructive',
    disqualified: 'destructive',
  }
  return variants[status] || 'secondary'
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const formatDateTime = (date: string) => {
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Check if submission was manually reviewed by a judge
const wasManuallyReviewed = (submission: Submission) => {
  return submission.reviewed_at && submission.reviewed_by
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
  <div class="container mx-auto px-6 py-10">
    <div class="mb-8">
      <span class="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs font-medium text-muted-foreground mb-4">
        <span class="h-1.5 w-1.5 rounded-full bg-brand" />
        Submissions
      </span>
      <h1 class="text-3xl md:text-4xl font-display font-semibold tracking-tight mb-3">My submissions</h1>
      <p class="text-lg text-muted-foreground">View and manage your competition entries</p>
    </div>

    <!-- Search and Filters -->
    <div class="flex flex-col sm:flex-row gap-4 mb-8">
      <div class="relative flex-1">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
        <Input
          v-model="searchQuery"
          placeholder="Search submissions..."
          class="pl-10 h-12 text-base"
        />
        <button
          v-if="searchQuery"
          @click="searchQuery = ''"
          aria-label="Clear search"
          class="absolute right-3 top-1/2 -translate-y-1/2 rounded-full text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          <X class="w-4 h-4" />
        </button>
      </div>
      <div class="flex gap-2 flex-wrap">
        <Button
          v-for="option in statusOptions"
          :key="option.value"
          :variant="statusFilter === option.value ? 'default' : 'outline'"
          size="sm"
          :aria-pressed="statusFilter === option.value"
          @click="statusFilter = option.value"
        >
          {{ option.label }}
        </Button>
      </div>
    </div>

    <Alert v-if="loadError || submissionsStore.error" variant="destructive" class="mb-8">
      <AlertDescription class="text-base">{{ loadError || submissionsStore.error }}</AlertDescription>
      <Button v-if="loadError" variant="outline" class="mt-4" @click="loadSubmissions">
        Try Again
      </Button>
    </Alert>

    <div v-if="submissionsStore.isLoading" class="text-center py-20">
      <Loader2 class="w-8 h-8 animate-spin text-muted-foreground mx-auto mb-4" />
      <p class="text-muted-foreground text-lg">Loading submissions...</p>
    </div>

    <div v-else-if="submissionsStore.submissions.length === 0" class="text-center py-20">
      <div class="w-16 h-16 rounded-full bg-secondary flex items-center justify-center mx-auto mb-6">
        <Camera class="w-8 h-8 text-muted-foreground" />
      </div>
      <h2 class="text-xl font-display font-semibold tracking-tight">No submissions yet</h2>
      <p class="text-muted-foreground mt-2">Submit your first photo to a competition!</p>
    </div>

    <div v-else-if="filteredSubmissions.length === 0" class="text-center py-20">
      <div class="w-16 h-16 rounded-full bg-secondary flex items-center justify-center mx-auto mb-6">
        <Search class="w-8 h-8 text-muted-foreground" />
      </div>
      <h2 class="text-xl font-display font-semibold tracking-tight">No matching submissions</h2>
      <p class="text-muted-foreground mt-2">Try adjusting your search or filters</p>
    </div>

    <!-- 3-Column Grid -->
    <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card
        v-for="submission in filteredSubmissions"
        :key="submission.id"
        class="overflow-hidden rounded-2xl cursor-pointer hover:shadow-lg transition-shadow"
        @click="openModal(submission)"
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
            <ImageIcon class="w-12 h-12 text-muted-foreground" />
          </div>
          <Badge
            :variant="getStatusVariant(submission.status)"
            class="absolute top-3 left-3"
          >
            {{ submission.status.toUpperCase() }}
          </Badge>
        </div>

        <CardContent class="p-5">
          <h3 class="text-lg font-semibold mb-2 line-clamp-1">{{ submission.title }}</h3>
          <div v-if="submission.competition" class="flex items-center gap-2 text-muted-foreground mb-3">
            <Trophy class="w-4 h-4" />
            <span class="text-sm line-clamp-1">{{ submission.competition.title }}</span>
          </div>
          <!-- Rejection reason preview -->
          <div v-if="submission.rejection_reason" class="flex items-start gap-2 text-destructive text-sm mb-3 p-2 bg-destructive/10 rounded-md">
            <XCircle class="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <span class="line-clamp-2">{{ submission.rejection_reason }}</span>
              <p v-if="submission.reviewed_at" class="text-xs opacity-70 mt-1">
                Reviewed {{ formatDate(submission.reviewed_at) }}
              </p>
            </div>
          </div>
          <!-- Manually approved indicator -->
          <div v-else-if="wasManuallyReviewed(submission) && submission.status === 'approved'" class="flex items-start gap-2 text-success text-sm mb-3 p-2 bg-success/10 rounded-md">
            <CheckCircle class="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <span>Approved by judge</span>
              <p v-if="submission.reviewed_at" class="text-xs opacity-70 mt-0.5">
                {{ formatDate(submission.reviewed_at) }}
              </p>
            </div>
          </div>
          <!-- Analysis error preview -->
          <div v-else-if="submission.analysis_error" class="flex items-start gap-2 text-warning text-sm mb-3 p-2 bg-warning/10 rounded-md">
            <AlertCircle class="w-4 h-4 shrink-0 mt-0.5" />
            <span class="line-clamp-2">Analysis failed — a judge will review this entry</span>
          </div>
          <div class="flex items-center justify-between text-sm text-muted-foreground">
            <div class="flex items-center">
              <Clock class="w-4 h-4 mr-2" />
              {{ formatDate(submission.created_at) }}
            </div>
            <!-- Simple camera info for users (verification handled in background) -->
            <div v-if="submission.camera_make" class="flex items-center gap-2">
              <Camera class="h-4 w-4" />
              <span>{{ submission.camera_make }} {{ submission.camera_model }}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Submission Detail Modal -->
    <Dialog :open="isModalOpen" @update:open="(open) => { if (!open) closeModal() }">
      <DialogContent class="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div class="flex items-center gap-3 mb-2">
            <Badge
              v-if="selectedSubmission"
              :variant="getStatusVariant(selectedSubmission.status)"
            >
              {{ selectedSubmission.status.toUpperCase() }}
            </Badge>
          </div>
          <DialogTitle class="text-2xl">{{ selectedSubmission?.title }}</DialogTitle>
          <DialogDescription v-if="selectedSubmission?.competition" class="flex items-center gap-2">
            <Trophy class="w-4 h-4" />
            {{ selectedSubmission.competition.title }}
          </DialogDescription>
        </DialogHeader>

        <div v-if="selectedSubmission" class="space-y-6 mt-4">
          <!-- Judge Review Card - Shows for both approved and rejected manual reviews -->
          <div v-if="wasManuallyReviewed(selectedSubmission)"
               class="rounded-xl border p-4"
               :class="selectedSubmission.status === 'approved'
                 ? 'border-success/30 bg-success/10'
                 : 'border-destructive/30 bg-destructive/10'">
            <div class="flex items-start gap-3">
              <div class="w-10 h-10 rounded-full flex items-center justify-center"
                   :class="selectedSubmission.status === 'approved' ? 'bg-success/20' : 'bg-destructive/20'">
                <Gavel class="w-5 h-5" :class="selectedSubmission.status === 'approved' ? 'text-success' : 'text-destructive'" />
              </div>
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-semibold" :class="selectedSubmission.status === 'approved' ? 'text-success' : 'text-destructive'">
                    {{ selectedSubmission.status === 'approved' ? 'Approved by judge' : 'Rejected by judge' }}
                  </span>
                </div>
                <p v-if="selectedSubmission.reviewed_at" class="text-sm text-muted-foreground mb-2">
                  Reviewed on {{ formatDateTime(selectedSubmission.reviewed_at) }}
                </p>
                <div v-if="selectedSubmission.rejection_reason" class="mt-3 p-3 rounded-lg bg-background/50">
                  <p class="text-sm font-medium mb-1 text-muted-foreground">Judge's Feedback:</p>
                  <p class="text-base">{{ selectedSubmission.rejection_reason }}</p>
                </div>
                <p v-else-if="selectedSubmission.status === 'approved'" class="text-sm text-muted-foreground">
                  Your submission has been manually approved and is now eligible for scoring.
                </p>
              </div>
            </div>
          </div>

          <!-- Analysis Error Alert (only if not yet reviewed) -->
          <Alert v-if="selectedSubmission.analysis_error && !wasManuallyReviewed(selectedSubmission)" variant="destructive">
            <AlertCircle class="w-4 h-4" />
            <AlertDescription>
              <strong>Analysis Error:</strong> {{ selectedSubmission.analysis_error }}
              <p class="text-xs mt-1 opacity-80">A judge will review this submission manually.</p>
            </AlertDescription>
          </Alert>

          <!-- Analyzing Status Info -->
          <Alert v-if="selectedSubmission.status === 'analyzing'" class="border-info/30 bg-info/10">
            <Info class="w-4 h-4 text-info" />
            <AlertDescription class="text-info">
              Your submission is being analyzed by our AI verification system. This usually takes a few minutes.
            </AlertDescription>
          </Alert>

          <!-- Pending Review Info (when pending and not analyzing) -->
          <Alert v-if="selectedSubmission.status === 'pending' && !selectedSubmission.analysis_error" class="border-warning/30 bg-warning/10">
            <Clock class="w-4 h-4 text-warning" />
            <AlertDescription class="text-warning">
              Your submission is pending review. A judge will evaluate it shortly.
            </AlertDescription>
          </Alert>

          <!-- Submitted Image -->
          <div v-if="selectedSubmission.jpg_file_url">
            <div class="rounded-xl overflow-hidden border bg-muted/20">
              <img
                :src="getImageUrl(selectedSubmission.jpg_file_url)"
                :alt="selectedSubmission.title"
                class="w-full h-auto object-contain"
                style="max-height: 500px;"
                @error="(e) => { (e.target as HTMLImageElement).style.display = 'none' }"
              />
            </div>
          </div>

          <!-- Description -->
          <div v-if="selectedSubmission.description">
            <h4 class="text-base font-medium text-muted-foreground mb-2">Description</h4>
            <p class="text-base leading-relaxed">{{ selectedSubmission.description }}</p>
          </div>

          <!-- Details Grid -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="p-4 bg-muted/30 rounded-xl">
              <p class="text-sm text-muted-foreground mb-1">Submitted</p>
              <p class="text-base font-medium">{{ formatDate(selectedSubmission.created_at) }}</p>
            </div>
            <div v-if="selectedSubmission.camera_make || selectedSubmission.camera_model" class="p-4 bg-muted/30 rounded-xl">
              <p class="text-sm text-muted-foreground mb-1">Camera</p>
              <p class="text-base font-medium flex items-center gap-2">
                <Camera class="w-4 h-4" />
                {{ [selectedSubmission.camera_make, selectedSubmission.camera_model].filter(Boolean).join(' ') }}
              </p>
            </div>
          </div>

          <!-- RAW File indicator -->
          <div v-if="selectedSubmission.raw_file_url" class="flex items-center gap-3 p-4 bg-muted/30 rounded-xl">
            <ImageIcon class="w-6 h-6 text-muted-foreground" />
            <span class="text-base">RAW file included</span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>
