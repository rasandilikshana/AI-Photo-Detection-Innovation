<template>
  <v-container class="py-8">
    <!-- Loading State -->
    <LoadingSpinner
      v-if="competitionStore.loading && !competition"
      message="Loading competition details..."
      fullPage
    />

    <!-- Error State -->
    <ErrorMessage
      v-else-if="competitionStore.error"
      :message="competitionStore.error"
      title="Failed to load competition"
      @close="competitionStore.clearError()"
    />

    <!-- Competition Details -->
    <div v-else-if="competition">
      <!-- Back Button -->
      <v-btn
        variant="text"
        prepend-icon="mdi-arrow-left"
        class="mb-4"
        @click="router.back()"
      >
        Back to Competitions
      </v-btn>

      <!-- Cover Image & Header -->
      <v-card elevation="2" class="mb-6">
        <v-img
          :src="coverImage"
          :alt="competition.title"
          height="400"
          cover
          gradient="to bottom, rgba(0,0,0,.1), rgba(0,0,0,.7)"
        >
          <div class="pa-8 d-flex flex-column justify-end fill-height">
            <v-chip
              :color="statusColor"
              size="large"
              class="mb-4 align-self-start text-uppercase font-weight-bold"
            >
              {{ competition.status }}
            </v-chip>
            <h1 class="text-h3 text-md-h2 font-weight-bold text-white mb-2">
              {{ competition.title }}
            </h1>
            <div class="d-flex align-center flex-wrap gap-4 text-white">
              <div class="d-flex align-center">
                <v-icon color="white" class="mr-2">mdi-image-multiple</v-icon>
                {{ competition.total_submissions }} submissions
              </div>
              <div class="d-flex align-center">
                <v-icon color="white" class="mr-2">mdi-account-group</v-icon>
                {{ competition.total_participants }} participants
              </div>
              <div v-if="competition.prize_amount" class="d-flex align-center">
                <v-icon color="white" class="mr-2">mdi-currency-usd</v-icon>
                ${{ competition.prize_amount.toLocaleString() }} Prize
              </div>
            </div>
          </div>
        </v-img>
      </v-card>

      <v-row>
        <!-- Main Content -->
        <v-col cols="12" md="8">
          <!-- Countdown Timer (if open) -->
          <v-card v-if="competition.status === 'open'" elevation="2" class="mb-6">
            <v-card-text class="text-center">
              <CountdownTimer
                :target-date="competition.submission_end"
                label="Submissions close in"
                expired-message="Submissions are now closed"
              />
            </v-card-text>
          </v-card>

          <!-- Description -->
          <v-card elevation="2" class="mb-6">
            <v-card-title class="text-h5 font-weight-bold">
              About This Competition
            </v-card-title>
            <v-divider />
            <v-card-text>
              <p class="text-body-1">{{ competition.description || 'No description provided.' }}</p>
            </v-card-text>
          </v-card>

          <!-- Rules -->
          <v-card v-if="competition.rules" elevation="2" class="mb-6">
            <v-card-title class="text-h5 font-weight-bold">
              Competition Rules
            </v-card-title>
            <v-divider />
            <v-card-text>
              <p class="text-body-1 white-space-pre-line">{{ competition.rules }}</p>
            </v-card-text>
          </v-card>

          <!-- Prize Information -->
          <v-card v-if="competition.prize_description" elevation="2" class="mb-6">
            <v-card-title class="text-h5 font-weight-bold">
              Prizes
            </v-card-title>
            <v-divider />
            <v-card-text>
              <p class="text-body-1">{{ competition.prize_description }}</p>
            </v-card-text>
          </v-card>

          <!-- Submissions Gallery -->
          <v-card elevation="2" class="mb-6">
            <v-card-title class="text-h5 font-weight-bold">
              Submissions
            </v-card-title>
            <v-divider />
            <v-card-text>
              <SubmissionGallery
                :submissions="submissions"
                :has-more="false"
              />
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Sidebar -->
        <v-col cols="12" md="4">
          <!-- Submit Button -->
          <v-card v-if="canSubmit" elevation="2" class="mb-6">
            <v-card-text>
              <v-btn
                :to="{ name: 'submission-create', query: { competition: competition.id } }"
                color="primary"
                size="large"
                block
              >
                <v-icon start>mdi-upload</v-icon>
                Submit Entry
              </v-btn>
            </v-card-text>
          </v-card>

          <!-- Important Dates -->
          <v-card elevation="2" class="mb-6">
            <v-card-title class="text-h6 font-weight-bold">
              Important Dates
            </v-card-title>
            <v-divider />
            <v-list density="compact">
              <v-list-item>
                <template #prepend>
                  <v-icon color="success">mdi-calendar-start</v-icon>
                </template>
                <v-list-item-title>Submissions Open</v-list-item-title>
                <v-list-item-subtitle>
                  {{ formatDate(competition.submission_start) }}
                </v-list-item-subtitle>
              </v-list-item>

              <v-list-item>
                <template #prepend>
                  <v-icon color="error">mdi-calendar-end</v-icon>
                </template>
                <v-list-item-title>Submissions Close</v-list-item-title>
                <v-list-item-subtitle>
                  {{ formatDate(competition.submission_end) }}
                </v-list-item-subtitle>
              </v-list-item>

              <v-list-item v-if="competition.judging_start">
                <template #prepend>
                  <v-icon color="info">mdi-gavel</v-icon>
                </template>
                <v-list-item-title>Judging Starts</v-list-item-title>
                <v-list-item-subtitle>
                  {{ formatDate(competition.judging_start) }}
                </v-list-item-subtitle>
              </v-list-item>

              <v-list-item v-if="competition.results_announcement">
                <template #prepend>
                  <v-icon color="warning">mdi-trophy</v-icon>
                </template>
                <v-list-item-title>Results Announced</v-list-item-title>
                <v-list-item-subtitle>
                  {{ formatDate(competition.results_announcement) }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card>

          <!-- Requirements -->
          <v-card elevation="2" class="mb-6">
            <v-card-title class="text-h6 font-weight-bold">
              Requirements
            </v-card-title>
            <v-divider />
            <v-list density="compact">
              <v-list-item>
                <template #prepend>
                  <v-icon>mdi-image</v-icon>
                </template>
                <v-list-item-title>Max File Size</v-list-item-title>
                <v-list-item-subtitle>
                  {{ competition.max_file_size_mb }} MB
                </v-list-item-subtitle>
              </v-list-item>

              <v-list-item>
                <template #prepend>
                  <v-icon>mdi-file-upload</v-icon>
                </template>
                <v-list-item-title>Max Submissions</v-list-item-title>
                <v-list-item-subtitle>
                  {{ competition.max_submissions_per_user }} per user
                </v-list-item-subtitle>
              </v-list-item>

              <v-list-item v-if="competition.require_raw_files">
                <template #prepend>
                  <v-icon color="warning">mdi-file-document</v-icon>
                </template>
                <v-list-item-title>Raw Files Required</v-list-item-title>
                <v-list-item-subtitle>
                  You must upload RAW files
                </v-list-item-subtitle>
              </v-list-item>

              <v-list-item v-if="competition.allowed_file_types">
                <template #prepend>
                  <v-icon>mdi-file-check</v-icon>
                </template>
                <v-list-item-title>Allowed Formats</v-list-item-title>
                <v-list-item-subtitle>
                  {{ competition.allowed_file_types.join(', ') }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card>

          <!-- Entry Fee -->
          <v-card v-if="competition.entry_fee" elevation="2" class="mb-6">
            <v-card-text class="text-center">
              <v-icon size="large" color="warning" class="mb-2">
                mdi-cash-multiple
              </v-icon>
              <h3 class="text-h5 font-weight-bold mb-1">
                ${{ competition.entry_fee }}
              </h3>
              <p class="text-caption text-medium-emphasis">Entry Fee</p>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { format } from 'date-fns'
import { useCompetitionStore } from '@/store/competition'
import { useSubmissionStore } from '@/store/submission'
import { useAuthStore } from '@/store/auth'
import { useToast } from 'vue-toastification'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorMessage from '@/components/common/ErrorMessage.vue'
import CountdownTimer from '@/components/common/CountdownTimer.vue'
import SubmissionGallery from '@/components/submission/SubmissionGallery.vue'

const route = useRoute()
const router = useRouter()
const competitionStore = useCompetitionStore()
const submissionStore = useSubmissionStore()
const authStore = useAuthStore()
const toast = useToast()

const competition = computed(() => competitionStore.currentCompetition)
const submissions = computed(() => submissionStore.submissions)

const coverImage = computed(() => {
  return competition.value?.cover_image_url || 'https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=1200'
})

const statusColor = computed(() => {
  if (!competition.value) return 'grey'

  switch (competition.value.status) {
    case 'open':
      return 'success'
    case 'draft':
      return 'warning'
    case 'judging':
      return 'info'
    case 'completed':
      return 'secondary'
    case 'closed':
      return 'error'
    default:
      return 'grey'
  }
})

const canSubmit = computed(() => {
  return authStore.isAuthenticated && competition.value?.status === 'open'
})

onMounted(async () => {
  const slug = route.params.slug as string

  try {
    // Fetch competition details
    await competitionStore.fetchCompetitionBySlug(slug)

    // Fetch submissions for this competition
    if (competition.value) {
      await submissionStore.fetchCompetitionSubmissions(competition.value.id)
    }
  } catch (error) {
    toast.error('Failed to load competition details')
  }
})

function formatDate(dateString: string): string {
  return format(new Date(dateString), 'PPP')
}
</script>

<style scoped>
.gap-4 {
  gap: 1rem;
}

.white-space-pre-line {
  white-space: pre-line;
}
</style>
