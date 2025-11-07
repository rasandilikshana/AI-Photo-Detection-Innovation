<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCompetitionsStore } from '@/stores/competitions'
import { useAuthStore } from '@/stores/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'

const route = useRoute()
const router = useRouter()
const competitionsStore = useCompetitionsStore()
const authStore = useAuthStore()

const competitionId = Number(route.params.id)

onMounted(async () => {
  await competitionsStore.fetchCompetitionById(competitionId)
})

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

const handleSubmit = () => {
  if (!authStore.isAuthenticated) {
    router.push('/login?redirect=' + route.fullPath)
    return
  }
  router.push(`/submit/${competitionId}`)
}
</script>

<template>
  <div class="container mx-auto px-4 py-12">
    <div v-if="competitionsStore.isLoading" class="text-center py-12">
      <p class="text-muted-foreground">Loading competition...</p>
    </div>

    <div v-else-if="competitionsStore.currentCompetition" class="max-w-4xl mx-auto">
      <div class="mb-6">
        <Button variant="ghost" @click="router.push('/competitions')">
          ← Back to Competitions
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div class="flex items-center justify-between mb-4">
            <Badge>{{ competitionsStore.currentCompetition.status.toUpperCase() }}</Badge>
          </div>
          <CardTitle class="text-3xl">{{ competitionsStore.currentCompetition.title }}</CardTitle>
          <CardDescription class="text-base mt-4">
            {{ competitionsStore.currentCompetition.description }}
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-6">
          <Separator />

          <div>
            <h3 class="font-semibold text-lg mb-4">Competition Details</h3>
            <div class="space-y-2 text-sm">
              <p><span class="font-medium">Submission Period:</span> {{ formatDate(competitionsStore.currentCompetition.submission_start) }} - {{ formatDate(competitionsStore.currentCompetition.submission_end) }}</p>
              <p><span class="font-medium">Max Submissions:</span> {{ competitionsStore.currentCompetition.max_submissions_per_user }}</p>
              <p><span class="font-medium">RAW Files:</span> {{ competitionsStore.currentCompetition.require_raw_files ? 'Required' : 'Optional' }}</p>
            </div>
          </div>

          <Separator />

          <div class="flex justify-center">
            <Button
              size="lg"
              @click="handleSubmit"
              :disabled="competitionsStore.currentCompetition.status !== 'open'"
            >
              {{ competitionsStore.currentCompetition.status === 'open' ? 'Submit Entry' : 'Submissions Closed' }}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
