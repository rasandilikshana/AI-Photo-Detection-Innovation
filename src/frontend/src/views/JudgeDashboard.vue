<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import apiClient from '@/api/client'

interface JudgeAssignment {
  assignment_id: number
  competition_id: number
  competition_title: string
  competition_status: string
  submission_start: string
  submission_end: string
}

interface PendingSubmission {
  id: number
  title: string
  description: string
  jpg_file_url: string
  camera_make: string
  camera_model: string
  created_at: string
}

const router = useRouter()
const authStore = useAuthStore()

const assignments = ref<JudgeAssignment[]>([])
const selectedCompetition = ref<number | null>(null)
const pendingSubmissions = ref<PendingSubmission[]>([])
const isLoading = ref(true)
const isLoadingSubmissions = ref(false)
const error = ref('')

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
    const response = await apiClient.get('/scores/my-assignments')
    assignments.value = response.data
  } catch (err: unknown) {
    error.value = 'Failed to load judge assignments'
    console.error('Failed to load assignments:', err)
  } finally {
    isLoading.value = false
  }
})

const loadPendingSubmissions = async (competitionId: number) => {
  try {
    isLoadingSubmissions.value = true
    selectedCompetition.value = competitionId
    const response = await apiClient.get(`/scores/pending/${competitionId}`)
    pendingSubmissions.value = response.data
  } catch (err) {
    error.value = 'Failed to load pending submissions'
    console.error('Failed to load submissions:', err)
  } finally {
    isLoadingSubmissions.value = false
  }
}

const getStatusBadgeClass = (status: string) => {
  const classes: Record<string, string> = {
    open: 'bg-green-500',
    judging: 'bg-blue-500',
    closed: 'bg-gray-500',
    completed: 'bg-purple-500',
  }
  return classes[status] || 'bg-gray-500'
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString()
}
</script>

<template>
  <div class="container mx-auto px-4 py-12">
    <div class="mb-8">
      <h1 class="text-4xl font-bold tracking-tight mb-4">Judge Dashboard</h1>
      <p class="text-lg text-muted-foreground">
        Score submissions for your assigned competitions
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
    <div v-if="isLoading" class="text-center py-12">
      <p class="text-muted-foreground">Loading your assignments...</p>
    </div>

    <template v-else-if="isJudge">
      <!-- No assignments -->
      <div v-if="assignments.length === 0" class="text-center py-12">
        <p class="text-muted-foreground">
          You are not assigned to any competitions yet.
        </p>
      </div>

      <!-- Assignments grid -->
      <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <Card
          v-for="assignment in assignments"
          :key="assignment.assignment_id"
          class="cursor-pointer hover:shadow-lg transition-shadow"
          :class="{ 'ring-2 ring-primary': selectedCompetition === assignment.competition_id }"
          @click="loadPendingSubmissions(assignment.competition_id)"
        >
          <CardHeader>
            <div class="flex justify-between items-start mb-2">
              <Badge :class="getStatusBadgeClass(assignment.competition_status)">
                {{ assignment.competition_status.toUpperCase() }}
              </Badge>
            </div>
            <CardTitle class="line-clamp-2">{{ assignment.competition_title }}</CardTitle>
            <CardDescription>
              {{ formatDate(assignment.submission_start) }} - {{ formatDate(assignment.submission_end) }}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" class="w-full">
              View Submissions
            </Button>
          </CardContent>
        </Card>
      </div>

      <!-- Pending submissions section -->
      <div v-if="selectedCompetition" class="mt-8">
        <h2 class="text-2xl font-semibold mb-4">
          Submissions to Score
        </h2>

        <div v-if="isLoadingSubmissions" class="text-center py-8">
          <p class="text-muted-foreground">Loading submissions...</p>
        </div>

        <div v-else-if="pendingSubmissions.length === 0" class="text-center py-8">
          <p class="text-muted-foreground">
            All submissions have been scored! Great work.
          </p>
        </div>

        <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card v-for="submission in pendingSubmissions" :key="submission.id">
            <CardHeader>
              <CardTitle class="line-clamp-2">{{ submission.title }}</CardTitle>
              <CardDescription v-if="submission.camera_make">
                {{ submission.camera_make }} {{ submission.camera_model }}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p v-if="submission.description" class="text-sm text-muted-foreground mb-4 line-clamp-2">
                {{ submission.description }}
              </p>
              <p class="text-xs text-muted-foreground mb-4">
                Submitted: {{ formatDate(submission.created_at) }}
              </p>
              <Button
                class="w-full"
                @click="router.push(`/judge/score/${submission.id}`)"
              >
                Score This Entry
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </template>
  </div>
</template>
