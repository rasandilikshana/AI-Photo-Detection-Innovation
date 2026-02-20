<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Trophy, Plus, Calendar, Eye } from 'lucide-vue-next'
import apiClient from '@/api/client'

interface Competition {
  id: number
  title: string
  description: string
  status: string
  submission_start: string
  submission_end: string
  prize_amount?: number
}

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref<'create' | 'my-competitions'>('create')
const myCompetitions = ref<Competition[]>([])
const isLoading = ref(false)
const isSubmitting = ref(false)
const error = ref('')
const success = ref('')

// Form data
const formData = ref({
  title: '',
  description: '',
  rules: '',
  submission_start: '',
  submission_end: '',
  max_submissions_per_user: 5,
  require_raw_files: true,
  allow_ai_generated: false,
  entry_fee: 0,
  prize_description: '',
  prize_amount: 0,
})

const isOrganizer = computed(() => {
  return authStore.user?.role === 'organizer' || authStore.user?.role === 'admin'
})

onMounted(async () => {
  if (!isOrganizer.value) {
    router.push('/')
    return
  }
  await loadMyCompetitions()
})

const loadMyCompetitions = async () => {
  try {
    isLoading.value = true
    const response = await apiClient.get('/competitions')
    // Filter to show only competitions created by current user (for organizers)
    // Admin sees all
    myCompetitions.value = response.data
  } catch (err) {
    console.error('Failed to load competitions:', err)
  } finally {
    isLoading.value = false
  }
}

const handleSubmit = async () => {
  try {
    isSubmitting.value = true
    error.value = ''
    success.value = ''

    // Validate dates
    if (new Date(formData.value.submission_end) <= new Date(formData.value.submission_start)) {
      error.value = 'End date must be after start date'
      return
    }

    await apiClient.post('/competitions', {
      ...formData.value,
      submission_start: new Date(formData.value.submission_start).toISOString(),
      submission_end: new Date(formData.value.submission_end).toISOString(),
      prize_amount: formData.value.prize_amount * 100, // Convert to cents
    })

    success.value = 'Competition created successfully!'

    // Reset form
    formData.value = {
      title: '',
      description: '',
      rules: '',
      submission_start: '',
      submission_end: '',
      max_submissions_per_user: 5,
      require_raw_files: true,
      allow_ai_generated: false,
      entry_fee: 0,
      prize_description: '',
      prize_amount: 0,
    }

    // Reload competitions
    await loadMyCompetitions()
    activeTab.value = 'my-competitions'
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'response' in err) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      error.value = axiosErr.response?.data?.detail || 'Failed to create competition'
    } else {
      error.value = 'Failed to create competition'
    }
  } finally {
    isSubmitting.value = false
  }
}

const getStatusVariant = (status: string) => {
  const variants: Record<string, string> = {
    open: 'default',
    draft: 'outline',
    closed: 'secondary',
    judging: 'secondary',
    completed: 'outline',
  }
  return variants[status] || 'secondary'
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
</script>

<template>
  <div class="container mx-auto px-6 py-10">
    <div class="mb-8">
      <div class="flex items-center gap-3 mb-2">
        <div class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
          <Trophy class="w-6 h-6 text-primary" />
        </div>
        <div>
          <h1 class="text-3xl font-bold text-foreground">Organizer Panel</h1>
          <p class="text-lg text-muted-foreground">
            Create and manage photography competitions
          </p>
        </div>
      </div>
    </div>

    <!-- Not organizer warning -->
    <Alert v-if="!isOrganizer" variant="destructive" class="mb-6">
      <AlertDescription>
        You don't have organizer permissions.
      </AlertDescription>
    </Alert>

    <template v-else>
      <!-- Tab Navigation -->
      <div class="flex gap-2 mb-8 border-b">
        <Button
          variant="ghost"
          :class="[
            'rounded-none border-b-2 transition-all',
            activeTab === 'create' ? 'border-primary text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground'
          ]"
          @click="activeTab = 'create'"
        >
          <Plus class="w-4 h-4 mr-2" />
          Create Competition
        </Button>
        <Button
          variant="ghost"
          :class="[
            'rounded-none border-b-2 transition-all',
            activeTab === 'my-competitions' ? 'border-primary text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground'
          ]"
          @click="activeTab = 'my-competitions'"
        >
          <Trophy class="w-4 h-4 mr-2" />
          My Competitions
        </Button>
      </div>

      <!-- Create Competition Tab -->
      <div v-if="activeTab === 'create'">
        <Card class="max-w-2xl">
          <CardHeader>
            <CardTitle>Create New Competition</CardTitle>
            <CardDescription>
              Fill in the details to create a new photography competition
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Alert v-if="error" variant="destructive" class="mb-6">
              <AlertDescription>{{ error }}</AlertDescription>
            </Alert>

            <Alert v-if="success" class="mb-6 bg-green-50 text-green-800 border-green-200">
              <AlertDescription>{{ success }}</AlertDescription>
            </Alert>

            <form @submit.prevent="handleSubmit" class="space-y-6">
              <div class="space-y-2">
                <Label for="title">Title *</Label>
                <Input
                  id="title"
                  v-model="formData.title"
                  placeholder="Nature Photography Contest 2024"
                  required
                  :disabled="isSubmitting"
                />
              </div>

              <div class="space-y-2">
                <Label for="description">Description *</Label>
                <Textarea
                  id="description"
                  v-model="formData.description"
                  placeholder="Describe your competition, themes, and what you're looking for..."
                  rows="4"
                  required
                  :disabled="isSubmitting"
                />
              </div>

              <div class="space-y-2">
                <Label for="rules">Rules</Label>
                <Textarea
                  id="rules"
                  v-model="formData.rules"
                  placeholder="Competition rules and guidelines..."
                  rows="3"
                  :disabled="isSubmitting"
                />
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label for="submission_start">Submission Start *</Label>
                  <Input
                    id="submission_start"
                    type="datetime-local"
                    v-model="formData.submission_start"
                    required
                    :disabled="isSubmitting"
                  />
                </div>
                <div class="space-y-2">
                  <Label for="submission_end">Submission End *</Label>
                  <Input
                    id="submission_end"
                    type="datetime-local"
                    v-model="formData.submission_end"
                    required
                    :disabled="isSubmitting"
                  />
                </div>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label for="max_submissions">Max Submissions per User</Label>
                  <Input
                    id="max_submissions"
                    type="number"
                    min="1"
                    max="20"
                    v-model.number="formData.max_submissions_per_user"
                    :disabled="isSubmitting"
                  />
                </div>
                <div class="space-y-2">
                  <Label for="prize_amount">Prize Amount ($)</Label>
                  <Input
                    id="prize_amount"
                    type="number"
                    min="0"
                    v-model.number="formData.prize_amount"
                    :disabled="isSubmitting"
                  />
                </div>
              </div>

              <div class="space-y-2">
                <Label for="prize_description">Prize Description</Label>
                <Input
                  id="prize_description"
                  v-model="formData.prize_description"
                  placeholder="First place: $500, Second place: $250..."
                  :disabled="isSubmitting"
                />
              </div>

              <div class="flex items-center gap-6">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    v-model="formData.require_raw_files"
                    class="w-4 h-4 rounded border-gray-300"
                    :disabled="isSubmitting"
                  />
                  <span class="text-sm">Require RAW files</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    v-model="formData.allow_ai_generated"
                    class="w-4 h-4 rounded border-gray-300"
                    :disabled="isSubmitting"
                  />
                  <span class="text-sm">Allow AI-generated images</span>
                </label>
              </div>

              <Button type="submit" class="w-full" :disabled="isSubmitting">
                {{ isSubmitting ? 'Creating...' : 'Create Competition' }}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>

      <!-- My Competitions Tab -->
      <div v-if="activeTab === 'my-competitions'">
        <div v-if="isLoading" class="text-center py-12">
          <div class="w-10 h-10 border-3 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p class="text-muted-foreground">Loading competitions...</p>
        </div>

        <div v-else-if="myCompetitions.length === 0" class="text-center py-12">
          <div class="w-20 h-20 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
            <Trophy class="w-10 h-10 text-muted-foreground" />
          </div>
          <p class="text-lg text-muted-foreground">No competitions yet</p>
          <p class="text-muted-foreground mt-1">Create your first competition to get started!</p>
          <Button class="mt-4" @click="activeTab = 'create'">
            <Plus class="w-4 h-4 mr-2" />
            Create Competition
          </Button>
        </div>

        <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card
            v-for="competition in myCompetitions"
            :key="competition.id"
            class="hover:shadow-lg transition-shadow"
          >
            <CardHeader>
              <div class="flex justify-between items-start mb-2">
                <Badge :variant="getStatusVariant(competition.status)">
                  {{ competition.status.toUpperCase() }}
                </Badge>
              </div>
              <CardTitle class="line-clamp-2">{{ competition.title }}</CardTitle>
              <CardDescription class="line-clamp-2">{{ competition.description }}</CardDescription>
            </CardHeader>
            <CardContent>
              <div class="flex items-center gap-2 text-sm text-muted-foreground mb-4">
                <Calendar class="w-4 h-4" />
                {{ formatDate(competition.submission_start) }} - {{ formatDate(competition.submission_end) }}
              </div>
              <Button
                variant="outline"
                class="w-full"
                @click="router.push(`/competitions/${competition.id}`)"
              >
                <Eye class="w-4 h-4 mr-2" />
                View Details
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </template>
  </div>
</template>
