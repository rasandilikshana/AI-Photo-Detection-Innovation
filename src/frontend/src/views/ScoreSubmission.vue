<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import apiClient from '@/api/client'

interface Submission {
  id: number
  title: string
  description: string
  jpg_file_url: string
  camera_make: string
  camera_model: string
  lens_model: string
  iso: number
  aperture: string
  shutter_speed: string
  created_at: string
}

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const submissionId = Number(route.params.submissionId)

const submission = ref<Submission | null>(null)
const compositionScore = ref<number>(5)
const technicalScore = ref<number>(5)
const creativityScore = ref<number>(5)
const comments = ref('')
const isLoading = ref(true)
const isSubmitting = ref(false)
const error = ref('')
const success = ref('')

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
    const response = await apiClient.get(`/submissions/${submissionId}`)
    submission.value = response.data
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

    await apiClient.post(`/scores/${submissionId}`, {
      composition_score: compositionScore.value,
      technical_score: technicalScore.value,
      creativity_score: creativityScore.value,
      comments: comments.value || null,
    })

    success.value = 'Score submitted successfully!'
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

const getImageUrl = (path: string) => {
  // Handle relative paths
  if (path.startsWith('./') || path.startsWith('/')) {
    return `http://localhost:8080${path.replace('./', '/')}`
  }
  return path
}
</script>

<template>
  <div class="container mx-auto px-4 py-12 max-w-4xl">
    <div class="mb-6">
      <Button variant="ghost" @click="router.back()">
        ← Back to Dashboard
      </Button>
    </div>

    <!-- Loading state -->
    <div v-if="isLoading" class="text-center py-12">
      <p class="text-muted-foreground">Loading submission...</p>
    </div>

    <!-- Error alert -->
    <Alert v-else-if="error && !submission" variant="destructive" class="mb-6">
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <template v-else-if="submission">
      <div class="grid lg:grid-cols-2 gap-8">
        <!-- Submission Details -->
        <Card>
          <CardHeader>
            <CardTitle>{{ submission.title }}</CardTitle>
            <CardDescription v-if="submission.description">
              {{ submission.description }}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <!-- Image preview placeholder -->
            <div class="bg-muted rounded-lg h-64 flex items-center justify-center mb-4">
              <span class="text-muted-foreground">Image Preview</span>
            </div>

            <!-- Camera info -->
            <div class="space-y-2 text-sm">
              <div v-if="submission.camera_make">
                <span class="font-medium">Camera:</span>
                <span class="ml-2">{{ submission.camera_make }} {{ submission.camera_model }}</span>
              </div>
              <div v-if="submission.lens_model">
                <span class="font-medium">Lens:</span>
                <span class="ml-2">{{ submission.lens_model }}</span>
              </div>
              <div v-if="submission.iso">
                <span class="font-medium">ISO:</span>
                <span class="ml-2">{{ submission.iso }}</span>
              </div>
              <div v-if="submission.aperture">
                <span class="font-medium">Aperture:</span>
                <span class="ml-2">{{ submission.aperture }}</span>
              </div>
              <div v-if="submission.shutter_speed">
                <span class="font-medium">Shutter:</span>
                <span class="ml-2">{{ submission.shutter_speed }}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Scoring Form -->
        <Card>
          <CardHeader>
            <CardTitle>Score This Submission</CardTitle>
            <CardDescription>
              Rate each category from 0 to 10
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Alert v-if="error" variant="destructive" class="mb-4">
              <AlertDescription>{{ error }}</AlertDescription>
            </Alert>

            <Alert v-if="success" class="mb-4 bg-green-50 text-green-800 border-green-200">
              <AlertDescription>{{ success }}</AlertDescription>
            </Alert>

            <form @submit.prevent="handleSubmit" class="space-y-6">
              <!-- Composition Score -->
              <div class="space-y-2">
                <div class="flex justify-between">
                  <Label for="composition">Composition (40% weight)</Label>
                  <span class="text-sm font-medium">{{ compositionScore }}</span>
                </div>
                <Input
                  id="composition"
                  type="range"
                  min="0"
                  max="10"
                  step="0.5"
                  v-model.number="compositionScore"
                  class="w-full"
                  :disabled="isSubmitting"
                />
                <p class="text-xs text-muted-foreground">
                  Framing, balance, rule of thirds, leading lines
                </p>
              </div>

              <!-- Technical Score -->
              <div class="space-y-2">
                <div class="flex justify-between">
                  <Label for="technical">Technical Skill (30% weight)</Label>
                  <span class="text-sm font-medium">{{ technicalScore }}</span>
                </div>
                <Input
                  id="technical"
                  type="range"
                  min="0"
                  max="10"
                  step="0.5"
                  v-model.number="technicalScore"
                  class="w-full"
                  :disabled="isSubmitting"
                />
                <p class="text-xs text-muted-foreground">
                  Focus, exposure, lighting, color accuracy
                </p>
              </div>

              <!-- Creativity Score -->
              <div class="space-y-2">
                <div class="flex justify-between">
                  <Label for="creativity">Creativity (30% weight)</Label>
                  <span class="text-sm font-medium">{{ creativityScore }}</span>
                </div>
                <Input
                  id="creativity"
                  type="range"
                  min="0"
                  max="10"
                  step="0.5"
                  v-model.number="creativityScore"
                  class="w-full"
                  :disabled="isSubmitting"
                />
                <p class="text-xs text-muted-foreground">
                  Originality, artistic vision, emotional impact
                </p>
              </div>

              <!-- Overall Score Preview -->
              <div class="p-4 bg-muted rounded-lg text-center">
                <p class="text-sm text-muted-foreground">Overall Score</p>
                <p class="text-3xl font-bold">{{ overallScorePreview }}</p>
              </div>

              <!-- Comments -->
              <div class="space-y-2">
                <Label for="comments">Comments (Optional)</Label>
                <Textarea
                  id="comments"
                  v-model="comments"
                  placeholder="Provide feedback for the photographer..."
                  rows="4"
                  :disabled="isSubmitting"
                />
              </div>

              <!-- Submit button -->
              <div class="flex gap-4">
                <Button
                  type="button"
                  variant="outline"
                  @click="router.back()"
                  :disabled="isSubmitting"
                >
                  Cancel
                </Button>
                <Button type="submit" class="flex-1" :disabled="isSubmitting">
                  {{ isSubmitting ? 'Submitting...' : 'Submit Score' }}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </template>
  </div>
</template>
