<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCompetitionsStore } from '@/stores/competitions'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Calendar, Trophy, Image, Search, X } from 'lucide-vue-next'

const router = useRouter()
const competitionsStore = useCompetitionsStore()
const searchQuery = ref('')
const statusFilter = ref<string>('all')

const statusOptions = [
  { value: 'all', label: 'All' },
  { value: 'open', label: 'Open' },
  { value: 'closed', label: 'Closed' },
  { value: 'judging', label: 'Judging' },
  { value: 'completed', label: 'Completed' },
]

const filteredCompetitions = computed(() => {
  let competitions = competitionsStore.competitions

  // Filter by search query
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    competitions = competitions.filter(c =>
      c.title.toLowerCase().includes(query) ||
      c.description?.toLowerCase().includes(query)
    )
  }

  // Filter by status
  if (statusFilter.value !== 'all') {
    competitions = competitions.filter(c => c.status === statusFilter.value)
  }

  return competitions
})

onMounted(async () => {
  await competitionsStore.fetchCompetitions({})
})

const getStatusVariant = (status: string) => {
  const variants: Record<string, string> = {
    open: 'default',
    closed: 'destructive',
    judging: 'secondary',
    completed: 'secondary',
    draft: 'outline',
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
</script>

<template>
  <div class="container mx-auto px-6 py-10">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-foreground mb-3">Photography Competitions</h1>
      <p class="text-lg text-muted-foreground">Browse competitions and submit your authentic photography</p>
    </div>

    <!-- Search and Filters -->
    <div class="flex flex-col sm:flex-row gap-4 mb-8">
      <div class="relative flex-1">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
        <Input
          v-model="searchQuery"
          placeholder="Search competitions..."
          class="pl-10 h-12 text-base"
        />
        <button
          v-if="searchQuery"
          @click="searchQuery = ''"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
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
          class="h-12 px-4 text-base"
          @click="statusFilter = option.value"
        >
          {{ option.label }}
        </Button>
      </div>
    </div>

    <Alert v-if="competitionsStore.error" variant="destructive" class="mb-8">
      <AlertDescription class="text-base">{{ competitionsStore.error }}</AlertDescription>
    </Alert>

    <div v-if="competitionsStore.isLoading" class="text-center py-20">
      <div class="w-12 h-12 border-3 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-6" />
      <p class="text-muted-foreground text-lg">Loading competitions...</p>
    </div>

    <div v-else-if="competitionsStore.competitions.length === 0" class="text-center py-20">
      <div class="w-24 h-24 rounded-full bg-muted flex items-center justify-center mx-auto mb-6">
        <Image class="w-12 h-12 text-muted-foreground" />
      </div>
      <p class="text-xl text-muted-foreground">No competitions at the moment</p>
      <p class="text-muted-foreground mt-2">Check back soon for new competitions!</p>
    </div>

    <div v-else-if="filteredCompetitions.length === 0" class="text-center py-20">
      <div class="w-24 h-24 rounded-full bg-muted flex items-center justify-center mx-auto mb-6">
        <Search class="w-12 h-12 text-muted-foreground" />
      </div>
      <p class="text-xl text-muted-foreground">No matching competitions</p>
      <p class="text-muted-foreground mt-2">Try adjusting your search or filters</p>
    </div>

    <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card
        v-for="competition in filteredCompetitions"
        :key="competition.id"
        class="flex flex-col cursor-pointer hover:shadow-lg transition-shadow"
        @click="router.push(`/competitions/${competition.id}`)"
      >
        <CardHeader class="p-6 pb-4">
          <div class="flex items-start justify-between mb-3">
            <Badge :variant="getStatusVariant(competition.status)" class="text-sm px-3 py-1">
              {{ competition.status }}
            </Badge>
          </div>
          <CardTitle class="text-xl font-semibold line-clamp-2 mb-2">
            {{ competition.title }}
          </CardTitle>
          <CardDescription class="line-clamp-3 text-base leading-relaxed">
            {{ competition.description }}
          </CardDescription>
        </CardHeader>
        <CardContent class="flex-1 px-6 pb-4">
          <div class="space-y-3 text-base text-muted-foreground">
            <div class="flex items-center gap-3">
              <Calendar class="w-5 h-5" />
              <span>Deadline: {{ formatDate(competition.submission_end) }}</span>
            </div>
            <div v-if="competition.prize_amount" class="flex items-center gap-3">
              <Trophy class="w-5 h-5 text-amber-500" />
              <span class="font-medium">${{ (competition.prize_amount / 100).toFixed(0) }} prize</span>
            </div>
          </div>
        </CardContent>
        <CardFooter class="p-6 pt-0">
          <Button variant="outline" class="w-full text-base py-5" @click.stop="router.push(`/competitions/${competition.id}`)">
            View Details
          </Button>
        </CardFooter>
      </Card>
    </div>
  </div>
</template>
