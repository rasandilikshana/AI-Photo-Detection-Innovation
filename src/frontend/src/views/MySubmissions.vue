<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useSubmissionsStore } from '@/stores/submissions'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'

const authStore = useAuthStore()
const submissionsStore = useSubmissionsStore()

onMounted(async () => {
  if (authStore.user) {
    await submissionsStore.fetchSubmissions({ user_id: authStore.user.id })
  }
})

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'bg-yellow-500',
    analyzing: 'bg-blue-500',
    approved: 'bg-green-500',
    rejected: 'bg-red-500',
    disqualified: 'bg-red-700',
  }
  return colors[status] || 'bg-gray-500'
}

const getVerdictColor = (verdict?: string) => {
  if (!verdict) return 'bg-gray-500'
  const colors: Record<string, string> = {
    authentic: 'bg-green-500',
    suspicious: 'bg-yellow-500',
    ai_generated: 'bg-red-500',
    needs_review: 'bg-orange-500',
  }
  return colors[verdict] || 'bg-gray-500'
}
</script>

<template>
  <div class="container mx-auto px-4 py-12">
    <div class="mb-8">
      <h1 class="text-4xl font-bold tracking-tight mb-4">My Submissions</h1>
      <p class="text-lg text-muted-foreground">
        View and manage your competition entries
      </p>
    </div>

    <Alert v-if="submissionsStore.error" variant="destructive" class="mb-6">
      <AlertDescription>{{ submissionsStore.error }}</AlertDescription>
    </Alert>

    <div v-if="submissionsStore.isLoading" class="text-center py-12">
      <p class="text-muted-foreground">Loading submissions...</p>
    </div>

    <div v-else-if="submissionsStore.submissions.length === 0" class="text-center py-12">
      <p class="text-muted-foreground">You haven't submitted any entries yet.</p>
    </div>

    <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card v-for="submission in submissionsStore.submissions" :key="submission.id">
        <CardHeader>
          <div class="flex items-center justify-between mb-2">
            <Badge :class="getStatusColor(submission.status)">
              {{ submission.status.toUpperCase() }}
            </Badge>
            <Badge v-if="submission.verification_verdict" :class="getVerdictColor(submission.verification_verdict)">
              {{ submission.verification_verdict.replace('_', ' ').toUpperCase() }}
            </Badge>
          </div>
          <CardTitle class="line-clamp-2">{{ submission.title }}</CardTitle>
          <CardDescription v-if="submission.competition">
            {{ submission.competition.title }}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div class="space-y-2 text-sm">
            <div v-if="submission.verification_confidence">
              <span class="font-medium">Confidence:</span>
              <span class="ml-2">{{ (submission.verification_confidence * 100).toFixed(1) }}%</span>
            </div>
            <div v-if="submission.score_count > 0">
              <span class="font-medium">Score:</span>
              <span class="ml-2">{{ submission.average_score?.toFixed(2) }} ({{ submission.score_count }} judges)</span>
            </div>
            <div v-if="submission.camera_make">
              <span class="font-medium">Camera:</span>
              <span class="ml-2">{{ submission.camera_make }} {{ submission.camera_model }}</span>
            </div>
            <div class="text-xs text-muted-foreground mt-4">
              Submitted: {{ new Date(submission.created_at).toLocaleDateString() }}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
