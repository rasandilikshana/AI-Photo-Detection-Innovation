<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCompetitionsStore } from '@/stores/competitions'
import { useAuthStore } from '@/stores/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ArrowLeft, Calendar, Image, FileImage, Trophy, Loader2 } from 'lucide-vue-next'

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
      <Loader2 class="w-8 h-8 animate-spin text-muted-foreground mx-auto mb-4" />
      <p class="text-muted-foreground">Loading competition...</p>
    </div>

    <div v-else-if="competitionsStore.currentCompetition" class="max-w-4xl mx-auto animate-fade-in-up">
      <div class="mb-6">
        <Button variant="ghost" @click="router.push('/competitions')" class="group">
          <ArrowLeft class="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" />
          Back to competitions
        </Button>
      </div>

      <Card class="rounded-2xl">
        <CardHeader>
          <span class="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs font-medium text-muted-foreground w-fit mb-4">
            <span class="h-1.5 w-1.5 rounded-full bg-brand" />
            Competition
          </span>
          <div class="flex items-center justify-between mb-4">
            <Badge :variant="getStatusVariant(competitionsStore.currentCompetition.status)">
              {{ competitionsStore.currentCompetition.status.toUpperCase() }}
            </Badge>
            <div v-if="competitionsStore.currentCompetition.prize_amount" class="flex items-center gap-2">
              <Trophy class="w-5 h-5 text-warning" />
              <span class="font-display font-semibold text-xl text-foreground">
                ${{ (competitionsStore.currentCompetition.prize_amount / 100).toFixed(2) }}
              </span>
            </div>
          </div>
          <CardTitle class="text-3xl md:text-4xl font-display font-semibold tracking-tight text-balance">{{ competitionsStore.currentCompetition.title }}</CardTitle>
          <CardDescription class="text-base mt-4">
            {{ competitionsStore.currentCompetition.description }}
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-6">
          <Separator />

          <div>
            <h3 class="font-display font-semibold text-lg mb-4">Competition details</h3>
            <div class="grid md:grid-cols-2 gap-4">
              <div class="rounded-2xl border bg-card p-5">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
                    <Calendar class="w-5 h-5 text-foreground" />
                  </div>
                  <div>
                    <p class="text-sm text-muted-foreground">Submission period</p>
                    <p class="font-medium">{{ formatDate(competitionsStore.currentCompetition.submission_start) }}</p>
                    <p class="text-sm text-muted-foreground">to {{ formatDate(competitionsStore.currentCompetition.submission_end) }}</p>
                  </div>
                </div>
              </div>

              <div class="rounded-2xl border bg-card p-5">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
                    <Image class="w-5 h-5 text-foreground" />
                  </div>
                  <div>
                    <p class="text-sm text-muted-foreground">Max submissions</p>
                    <p class="font-medium">{{ competitionsStore.currentCompetition.max_submissions_per_user }} entries per user</p>
                  </div>
                </div>
              </div>

              <div class="rounded-2xl border bg-card p-5">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
                    <FileImage class="w-5 h-5 text-foreground" />
                  </div>
                  <div>
                    <p class="text-sm text-muted-foreground">RAW files</p>
                    <p class="font-medium">{{ competitionsStore.currentCompetition.require_raw_files ? 'Required' : 'Optional' }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <Separator />

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

    <div v-else class="max-w-4xl mx-auto text-center py-20">
      <div class="w-16 h-16 rounded-full bg-secondary flex items-center justify-center mx-auto mb-6">
        <Image class="w-8 h-8 text-muted-foreground" />
      </div>
      <h2 class="text-2xl font-display font-semibold tracking-tight mb-2">Competition not found</h2>
      <p class="text-muted-foreground mb-6">This competition may have been removed or the link is incorrect.</p>
      <a
        href="/competitions"
        class="inline-flex items-center justify-center rounded-full border border-input bg-card px-5 h-10 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      >
        Browse competitions
      </a>
    </div>
  </div>
</template>
