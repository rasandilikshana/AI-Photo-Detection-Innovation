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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Trophy, Plus, Calendar, Eye, Pencil, Loader2 } from 'lucide-vue-next'
import apiClient from '@/api/client'
import type { Competition } from '@/types'

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
    const all: Competition[] = response.data
    myCompetitions.value =
      authStore.user?.role === 'admin'
        ? all
        : all.filter((c) => c.organizer_id === authStore.user?.id)
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

// Edit competition
const showEditDialog = ref(false)
const editingCompetition = ref<Competition | null>(null)
const isSaving = ref(false)
const editError = ref('')
const editSuccess = ref('')

const editFormData = ref({
  title: '',
  description: '',
  rules: '',
  status: 'draft' as Competition['status'],
  submission_start: '',
  submission_end: '',
  max_submissions_per_user: 5,
  require_raw_files: true,
  allow_ai_generated: false,
  prize_description: '',
  prize_amount: 0,
})

const statusOptions: Competition['status'][] = [
  'draft',
  'open',
  'closed',
  'judging',
  'completed',
  'cancelled',
]

const toDatetimeLocal = (dateStr: string) => {
  const d = new Date(dateStr)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const openEditDialog = (competition: Competition) => {
  editingCompetition.value = competition
  editError.value = ''
  editFormData.value = {
    title: competition.title,
    description: competition.description,
    rules: competition.rules || '',
    status: competition.status,
    submission_start: toDatetimeLocal(competition.submission_start),
    submission_end: toDatetimeLocal(competition.submission_end),
    max_submissions_per_user: competition.max_submissions_per_user,
    require_raw_files: competition.require_raw_files,
    allow_ai_generated: competition.allow_ai_generated,
    prize_description: competition.prize_description || '',
    prize_amount: (competition.prize_amount || 0) / 100, // cents to dollars
  }
  showEditDialog.value = true
}

const closeEditDialog = () => {
  showEditDialog.value = false
  editingCompetition.value = null
  editError.value = ''
}

const handleEditSubmit = async () => {
  if (!editingCompetition.value) return

  try {
    isSaving.value = true
    editError.value = ''
    editSuccess.value = ''

    // Validate dates
    if (new Date(editFormData.value.submission_end) <= new Date(editFormData.value.submission_start)) {
      editError.value = 'End date must be after start date'
      return
    }

    await apiClient.patch(`/competitions/${editingCompetition.value.id}`, {
      title: editFormData.value.title,
      description: editFormData.value.description,
      rules: editFormData.value.rules,
      status: editFormData.value.status,
      submission_start: new Date(editFormData.value.submission_start).toISOString(),
      submission_end: new Date(editFormData.value.submission_end).toISOString(),
      max_submissions_per_user: editFormData.value.max_submissions_per_user,
      require_raw_files: editFormData.value.require_raw_files,
      allow_ai_generated: editFormData.value.allow_ai_generated,
      prize_description: editFormData.value.prize_description,
      prize_amount: Math.round(editFormData.value.prize_amount * 100), // Convert to cents
    })

    editSuccess.value = 'Competition updated successfully!'
    closeEditDialog()
    await loadMyCompetitions()
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'response' in err) {
      const axiosErr = err as { response?: { data?: { detail?: string | Array<{ msg?: string }> } } }
      const detail = axiosErr.response?.data?.detail
      editError.value =
        typeof detail === 'string'
          ? detail
          : detail?.[0]?.msg || 'Failed to update competition'
    } else {
      editError.value = 'Failed to update competition'
    }
  } finally {
    isSaving.value = false
  }
}

const getStatusVariant = (status: string) => {
  const variants: Record<string, string> = {
    open: 'success',
    draft: 'outline',
    closed: 'warning',
    judging: 'info',
    completed: 'secondary',
    cancelled: 'destructive',
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
      <span class="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs font-medium text-muted-foreground mb-3">
        <span class="h-1.5 w-1.5 rounded-full bg-brand" />
        Competition management
      </span>
      <h1 class="text-3xl md:text-4xl font-display font-semibold tracking-tight">Organizer panel</h1>
      <p class="mt-2 text-muted-foreground">
        Create and manage photography competitions
      </p>
    </div>

    <!-- Not organizer warning -->
    <Alert v-if="!isOrganizer" variant="destructive" class="mb-6">
      <AlertDescription>
        You don't have organizer permissions.
      </AlertDescription>
    </Alert>

    <template v-else>
      <!-- Tab Navigation -->
      <div class="inline-flex rounded-full border bg-card p-1 mb-8">
        <Button
          variant="ghost"
          :class="[
            'rounded-full transition-all',
            activeTab === 'create' ? 'bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground' : 'text-muted-foreground hover:bg-accent'
          ]"
          @click="activeTab = 'create'"
        >
          <Plus class="w-4 h-4 mr-2" />
          Create competition
        </Button>
        <Button
          variant="ghost"
          :class="[
            'rounded-full transition-all',
            activeTab === 'my-competitions' ? 'bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground' : 'text-muted-foreground hover:bg-accent'
          ]"
          @click="activeTab = 'my-competitions'"
        >
          <Trophy class="w-4 h-4 mr-2" />
          My competitions
        </Button>
      </div>

      <!-- Create Competition Tab -->
      <div v-if="activeTab === 'create'">
        <Card class="max-w-2xl rounded-2xl">
          <CardHeader>
            <CardTitle>Create new competition</CardTitle>
            <CardDescription>
              Fill in the details to create a new photography competition
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Alert v-if="error" variant="destructive" class="mb-6">
              <AlertDescription>{{ error }}</AlertDescription>
            </Alert>

            <Alert v-if="success" class="mb-6 bg-success/10 border-success/30 text-success">
              <AlertDescription>{{ success }}</AlertDescription>
            </Alert>

            <form @submit.prevent="handleSubmit" class="space-y-6">
              <div class="space-y-2">
                <Label for="title">Title *</Label>
                <Input
                  id="title"
                  v-model="formData.title"
                  placeholder="Wildlife Photography Competition 2026"
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

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label for="submission_start">Submission start *</Label>
                  <Input
                    id="submission_start"
                    type="datetime-local"
                    v-model="formData.submission_start"
                    required
                    :disabled="isSubmitting"
                  />
                </div>
                <div class="space-y-2">
                  <Label for="submission_end">Submission end *</Label>
                  <Input
                    id="submission_end"
                    type="datetime-local"
                    v-model="formData.submission_end"
                    required
                    :disabled="isSubmitting"
                  />
                </div>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label for="max_submissions">Max submissions per user</Label>
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
                  <Label for="prize_amount">Prize amount ($)</Label>
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
                <Label for="prize_description">Prize description</Label>
                <Input
                  id="prize_description"
                  v-model="formData.prize_description"
                  placeholder="First place: $500, Second place: $250..."
                  :disabled="isSubmitting"
                />
              </div>

              <div class="flex flex-wrap items-center gap-6">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    v-model="formData.require_raw_files"
                    class="w-4 h-4 rounded border-input accent-primary"
                    :disabled="isSubmitting"
                  />
                  <span class="text-sm">Require RAW files</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    v-model="formData.allow_ai_generated"
                    class="w-4 h-4 rounded border-input accent-primary"
                    :disabled="isSubmitting"
                  />
                  <span class="text-sm">Allow AI-generated images</span>
                </label>
              </div>

              <Button type="submit" class="w-full" :disabled="isSubmitting">
                {{ isSubmitting ? 'Creating...' : 'Create competition' }}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>

      <!-- My Competitions Tab -->
      <div v-if="activeTab === 'my-competitions'">
        <Alert v-if="editSuccess" class="mb-6 bg-success/10 border-success/30 text-success">
          <AlertDescription>{{ editSuccess }}</AlertDescription>
        </Alert>

        <div v-if="isLoading" class="text-center py-12">
          <Loader2 class="w-8 h-8 animate-spin text-muted-foreground mx-auto mb-4" />
          <p class="text-muted-foreground">Loading competitions...</p>
        </div>

        <div v-else-if="myCompetitions.length === 0" class="text-center py-12">
          <div class="w-16 h-16 rounded-full bg-secondary flex items-center justify-center mx-auto mb-4">
            <Trophy class="w-8 h-8 text-muted-foreground" />
          </div>
          <p class="text-lg text-muted-foreground">No competitions yet</p>
          <p class="text-muted-foreground mt-1">Create your first competition to get started!</p>
          <Button class="mt-4" @click="activeTab = 'create'">
            <Plus class="w-4 h-4 mr-2" />
            Create competition
          </Button>
        </div>

        <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card
            v-for="competition in myCompetitions"
            :key="competition.id"
            class="rounded-2xl transition-shadow hover:shadow-lg"
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
              <div class="flex gap-2">
                <Button
                  variant="outline"
                  class="flex-1"
                  @click="router.push(`/competitions/${competition.id}`)"
                >
                  <Eye class="w-4 h-4 mr-2" />
                  View details
                </Button>
                <Button
                  variant="outline"
                  class="flex-1"
                  @click="openEditDialog(competition)"
                >
                  <Pencil class="w-4 h-4 mr-2" />
                  Edit
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- Edit Competition Dialog -->
        <Dialog :open="showEditDialog" @update:open="(open: boolean) => { if (!open) closeEditDialog() }">
          <DialogContent class="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit competition</DialogTitle>
              <DialogDescription>
                Update the details of "{{ editingCompetition?.title }}"
              </DialogDescription>
            </DialogHeader>

            <Alert v-if="editError" variant="destructive" class="mb-4">
              <AlertDescription>{{ editError }}</AlertDescription>
            </Alert>

            <form @submit.prevent="handleEditSubmit" class="space-y-6">
              <div class="space-y-2">
                <Label for="edit_title">Title *</Label>
                <Input
                  id="edit_title"
                  v-model="editFormData.title"
                  required
                  :disabled="isSaving"
                />
              </div>

              <div class="space-y-2">
                <Label for="edit_description">Description *</Label>
                <Textarea
                  id="edit_description"
                  v-model="editFormData.description"
                  rows="4"
                  required
                  :disabled="isSaving"
                />
              </div>

              <div class="space-y-2">
                <Label for="edit_rules">Rules</Label>
                <Textarea
                  id="edit_rules"
                  v-model="editFormData.rules"
                  rows="3"
                  :disabled="isSaving"
                />
              </div>

              <div class="space-y-2">
                <Label for="edit_status">Status</Label>
                <select
                  id="edit_status"
                  v-model="editFormData.status"
                  :disabled="isSaving"
                  class="h-10 w-full rounded-xl border border-input bg-card px-3 py-2 text-sm cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option v-for="option in statusOptions" :key="option" :value="option">
                    {{ option.charAt(0).toUpperCase() + option.slice(1) }}
                  </option>
                </select>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label for="edit_submission_start">Submission start *</Label>
                  <Input
                    id="edit_submission_start"
                    type="datetime-local"
                    v-model="editFormData.submission_start"
                    required
                    :disabled="isSaving"
                  />
                </div>
                <div class="space-y-2">
                  <Label for="edit_submission_end">Submission end (deadline) *</Label>
                  <Input
                    id="edit_submission_end"
                    type="datetime-local"
                    v-model="editFormData.submission_end"
                    required
                    :disabled="isSaving"
                  />
                </div>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label for="edit_max_submissions">Max submissions per user</Label>
                  <Input
                    id="edit_max_submissions"
                    type="number"
                    min="1"
                    max="20"
                    v-model.number="editFormData.max_submissions_per_user"
                    :disabled="isSaving"
                  />
                </div>
                <div class="space-y-2">
                  <Label for="edit_prize_amount">Prize amount ($)</Label>
                  <Input
                    id="edit_prize_amount"
                    type="number"
                    min="0"
                    v-model.number="editFormData.prize_amount"
                    :disabled="isSaving"
                  />
                </div>
              </div>

              <div class="space-y-2">
                <Label for="edit_prize_description">Prize description</Label>
                <Input
                  id="edit_prize_description"
                  v-model="editFormData.prize_description"
                  :disabled="isSaving"
                />
              </div>

              <div class="flex flex-wrap items-center gap-6">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    v-model="editFormData.require_raw_files"
                    class="w-4 h-4 rounded border-input accent-primary"
                    :disabled="isSaving"
                  />
                  <span class="text-sm">Require RAW files</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    v-model="editFormData.allow_ai_generated"
                    class="w-4 h-4 rounded border-input accent-primary"
                    :disabled="isSaving"
                  />
                  <span class="text-sm">Allow AI-generated images</span>
                </label>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  :disabled="isSaving"
                  @click="closeEditDialog"
                >
                  Cancel
                </Button>
                <Button type="submit" :disabled="isSaving">
                  {{ isSaving ? 'Saving...' : 'Save changes' }}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </template>
  </div>
</template>
