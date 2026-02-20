<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCompetitionsStore } from '@/stores/competitions'
import { useAuthStore } from '@/stores/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ArrowLeft, Calendar, Image, FileImage, Trophy } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const competitionsStore = useCompetitionsStore()
const authStore = useAuthStore()

const competitionId = Number(route.params.id)

onMounted(async () => {
  await competitionsStore.fetchCompetitionById(competitionId)
})

// Check if competition is currently accepting submissions
const isAcceptingSubmissions = computed(() => {
  const comp = competitionsStore.currentCompetition
  if (!comp || comp.status !== 'open') return false

  const now = new Date()
  const start = new Date(comp.submission_start)
  const end = new Date(comp.submission_end)

  return start <= now && now <= end
})

// Get button text based on competition state
const submitButtonText = computed(() => {
  const comp = competitionsStore.currentCompetition
  if (!comp) return 'Loading...'

  if (comp.status !== 'open') return 'Submissions Closed'

  const now = new Date()
  const start = new Date(comp.submission_start)
  const end = new Date(comp.submission_end)

  if (now < start) return 'Opens ' + formatDate(comp.submission_start)
  if (now > end) return 'Deadline Passed'

  return 'Submit Entry'
})

const getStatusVariant = (status: string) => {
  const variants: Record<string, string> = {
    open: 'default',
    closed: 'destructive',
    judging: 'secondary',
    completed: 'outline',
    draft: 'secondary',
  }
  return variants[status] || 'secondary'
}

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
      <div class="w-12 h-12 rounded-full bg-gradient-to-br from-gradient-start to-gradient-end mx-auto mb-4 animate-glow-pulse" />
      <p class="text-muted-foreground">Loading competition...</p>
    </div>

    <div v-else-if="competitionsStore.currentCompetition" class="max-w-4xl mx-auto animate-fade-in-up">
      <div class="mb-6">
        <Button variant="ghost" @click="router.push('/competitions')" class="group">
          <ArrowLeft class="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" />
          Back to Competitions
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div class="flex items-center justify-between mb-4">
            <Badge :variant="getStatusVariant(competitionsStore.currentCompetition.status)">
              {{ competitionsStore.currentCompetition.status.toUpperCase() }}
            </Badge>
            <div v-if="competitionsStore.currentCompetition.prize_amount" class="flex items-center gap-2">
              <Trophy class="w-5 h-5 text-gradient-start" />
              <span class="gradient-text font-bold text-xl">
                ${{ (competitionsStore.currentCompetition.prize_amount / 100).toFixed(2) }}
              </span>
            </div>
          </div>
          <CardTitle class="text-3xl gradient-text">{{ competitionsStore.currentCompetition.title }}</CardTitle>
          <CardDescription class="text-base mt-4">
            {{ competitionsStore.currentCompetition.description }}
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-6">
          <Separator class="bg-white/10" />

          <div>
            <h3 class="font-semibold text-lg mb-4 gradient-text">Competition Details</h3>
            <div class="grid md:grid-cols-2 gap-4">
              <div class="p-4 rounded-lg bg-white/5 border border-white/10 space-y-3">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-gradient-start to-gradient-mid flex items-center justify-center">
                    <Calendar class="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p class="text-sm text-muted-foreground">Submission Period</p>
                    <p class="font-medium">{{ formatDate(competitionsStore.currentCompetition.submission_start) }}</p>
                    <p class="text-sm text-muted-foreground">to {{ formatDate(competitionsStore.currentCompetition.submission_end) }}</p>
                  </div>
                </div>
              </div>

              <div class="p-4 rounded-lg bg-white/5 border border-white/10 space-y-3">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-gradient-mid to-gradient-end flex items-center justify-center">
                    <Image class="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p class="text-sm text-muted-foreground">Max Submissions</p>
                    <p class="font-medium">{{ competitionsStore.currentCompetition.max_submissions_per_user }} entries per user</p>
                  </div>
                </div>
              </div>

              <div class="p-4 rounded-lg bg-white/5 border border-white/10 space-y-3">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-gradient-end to-gradient-start flex items-center justify-center">
                    <FileImage class="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p class="text-sm text-muted-foreground">RAW Files</p>
                    <p class="font-medium">{{ competitionsStore.currentCompetition.require_raw_files ? 'Required' : 'Optional' }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <Separator class="bg-white/10" />

          <div class="flex justify-center">
            <Button
              size="lg"
              @click="handleSubmit"
              :disabled="!isAcceptingSubmissions"
              class="min-w-[200px]"
            >
              {{ submitButtonText }}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
