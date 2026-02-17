<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSubmissionsStore } from '@/stores/submissions'
import { useCompetitionsStore } from '@/stores/competitions'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'

const route = useRoute()
const router = useRouter()
const submissionsStore = useSubmissionsStore()
const competitionsStore = useCompetitionsStore()

const competitionId = Number(route.params.competitionId)

const title = ref('')
const description = ref('')
const jpgFile = ref<File | null>(null)
const rawFile = ref<File | null>(null)
const isSubmitting = ref(false)
const isLoading = ref(true)
const loadError = ref('')

// Constants for file validation
const MAX_JPG_SIZE_MB = 50
const MAX_RAW_SIZE_MB = 200

onMounted(async () => {
  try {
    isLoading.value = true
    loadError.value = ''
    await competitionsStore.fetchCompetitionById(competitionId)
  } catch (error) {
    loadError.value = 'Failed to load competition details. Please try again.'
  } finally {
    isLoading.value = false
  }
})

const handleJpgFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  submissionsStore.clearError()

  if (target.files && target.files[0]) {
    const file = target.files[0]
    const fileSizeMB = file.size / (1024 * 1024)

    if (fileSizeMB > MAX_JPG_SIZE_MB) {
      submissionsStore.error = `JPG file too large. Maximum size is ${MAX_JPG_SIZE_MB}MB`
      target.value = ''
      jpgFile.value = null
      return
    }

    jpgFile.value = file
  }
}

const handleRawFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  submissionsStore.clearError()

  if (target.files && target.files[0]) {
    const file = target.files[0]
    const fileSizeMB = file.size / (1024 * 1024)

    if (fileSizeMB > MAX_RAW_SIZE_MB) {
      submissionsStore.error = `RAW file too large. Maximum size is ${MAX_RAW_SIZE_MB}MB`
      target.value = ''
      rawFile.value = null
      return
    }

    rawFile.value = file
  }
}

const handleSubmit = async () => {
  // Clear previous errors
  submissionsStore.clearError()

  // Validate required fields
  if (!title.value.trim()) {
    submissionsStore.error = 'Please enter a title for your submission'
    return
  }

  if (!jpgFile.value) {
    submissionsStore.error = 'Please select a JPG file to upload'
    return
  }

  if (competitionsStore.currentCompetition?.require_raw_files && !rawFile.value) {
    submissionsStore.error = 'RAW file is required for this competition'
    return
  }

  isSubmitting.value = true
  try {
    await submissionsStore.createSubmission({
      title: title.value.trim(),
      description: description.value.trim(),
      competition_id: competitionId,
      jpg_file: jpgFile.value,
      raw_file: rawFile.value || undefined,
    })
    router.push('/my-submissions')
  } catch (error: unknown) {
    // Error is already set in the store by createSubmission
    // Just log for debugging
    if (error instanceof Error) {
      console.error('Submission failed:', error.message)
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="container mx-auto px-4 py-12 max-w-2xl">
    <div class="mb-6">
      <Button variant="ghost" @click="router.back()">
        ← Back
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center items-center py-12">
      <div class="text-muted-foreground">Loading competition details...</div>
    </div>

    <!-- Load Error -->
    <Alert v-else-if="loadError" variant="destructive" class="mb-6">
      <AlertDescription>{{ loadError }}</AlertDescription>
      <Button variant="outline" size="sm" class="mt-4" @click="router.back()">
        Go Back
      </Button>
    </Alert>

    <Card v-else>
      <CardHeader>
        <CardTitle>Submit Your Entry</CardTitle>
        <CardDescription v-if="competitionsStore.currentCompetition">
          Submitting to: {{ competitionsStore.currentCompetition.title }}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Alert v-if="submissionsStore.error" variant="destructive" class="mb-6">
          <AlertDescription>{{ submissionsStore.error }}</AlertDescription>
        </Alert>

        <form @submit.prevent="handleSubmit" class="space-y-6">
          <div class="space-y-2">
            <Label for="title">Title*</Label>
            <Input
              id="title"
              v-model="title"
              placeholder="Enter your photo title"
              required
              :disabled="isSubmitting"
            />
          </div>

          <div class="space-y-2">
            <Label for="description">Description</Label>
            <Textarea
              id="description"
              v-model="description"
              placeholder="Describe your photo (optional)"
              rows="4"
              :disabled="isSubmitting"
            />
          </div>

          <div class="space-y-2">
            <Label for="jpgFile">JPG File*</Label>
            <Input
              id="jpgFile"
              type="file"
              accept=".jpg,.jpeg"
              @change="handleJpgFileChange"
              required
              :disabled="isSubmitting"
            />
            <p class="text-sm text-muted-foreground">
              Upload your photo in JPG or JPEG format
            </p>
          </div>

          <div class="space-y-2">
            <Label for="rawFile">
              RAW File{{ competitionsStore.currentCompetition?.require_raw_files ? '*' : '' }}
            </Label>
            <Input
              id="rawFile"
              type="file"
              accept=".raw,.cr2,.nef,.arw,.dng"
              @change="handleRawFileChange"
              :required="competitionsStore.currentCompetition?.require_raw_files"
              :disabled="isSubmitting"
            />
            <p class="text-sm text-muted-foreground">
              Upload your RAW file for verification
            </p>
          </div>

          <div class="flex gap-4">
            <Button type="button" variant="outline" @click="router.back()" :disabled="isSubmitting">
              Cancel
            </Button>
            <Button type="submit" class="flex-1" :disabled="isSubmitting">
              {{ isSubmitting ? 'Submitting...' : 'Submit Entry' }}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  </div>
</template>
