<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCompetitionsStore } from '@/stores/competitions'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'

const router = useRouter()
const competitionsStore = useCompetitionsStore()

onMounted(async () => {
  await competitionsStore.fetchCompetitions({ status: 'open' })
})

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    open: 'bg-green-500',
    closed: 'bg-red-500',
    judging: 'bg-yellow-500',
    completed: 'bg-blue-500',
    draft: 'bg-gray-500',
  }
  return colors[status] || 'bg-gray-500'
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
</script>

<template>
  <div class="container mx-auto px-4 py-12">
    <div class="mb-8">
      <h1 class="text-4xl font-bold tracking-tight mb-4">Photography Competitions</h1>
      <p class="text-lg text-muted-foreground">
        Browse active competitions and submit your authentic photography
      </p>
    </div>

    <Alert v-if="competitionsStore.error" variant="destructive" class="mb-6">
      <AlertDescription>{{ competitionsStore.error }}</AlertDescription>
    </Alert>

    <div v-if="competitionsStore.isLoading" class="text-center py-12">
      <p class="text-muted-foreground">Loading competitions...</p>
    </div>

    <div v-else-if="competitionsStore.competitions.length === 0" class="text-center py-12">
      <p class="text-muted-foreground">No active competitions at the moment.</p>
    </div>

    <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card
        v-for="competition in competitionsStore.competitions"
        :key="competition.id"
        class="flex flex-col cursor-pointer hover:shadow-lg transition-shadow"
        @click="router.push(`/competitions/${competition.id}`)"
      >
        <CardHeader>
          <div class="flex items-start justify-between mb-2">
            <Badge :class="getStatusColor(competition.status)">
              {{ competition.status.toUpperCase() }}
            </Badge>
          </div>
          <CardTitle class="line-clamp-2">{{ competition.title }}</CardTitle>
          <CardDescription class="line-clamp-3">
            {{ competition.description }}
          </CardDescription>
        </CardHeader>
        <CardContent class="flex-1">
          <div class="space-y-2 text-sm text-muted-foreground">
            <div class="flex items-center gap-2">
              <span class="font-medium">Submission Deadline:</span>
              <span>{{ formatDate(competition.submission_end) }}</span>
            </div>
            <div v-if="competition.prize_amount" class="flex items-center gap-2">
              <span class="font-medium">Prize:</span>
              <span>${{ (competition.prize_amount / 100).toFixed(2) }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="font-medium">Max Submissions:</span>
              <span>{{ competition.max_submissions_per_user }}</span>
            </div>
            <div v-if="competition.require_raw_files" class="flex items-center gap-2">
              <Badge variant="outline">RAW Required</Badge>
            </div>
          </div>
        </CardContent>
        <CardFooter>
          <Button class="w-full" @click.stop="router.push(`/competitions/${competition.id}`)">
            View Details
          </Button>
        </CardFooter>
      </Card>
    </div>
  </div>
</template>
