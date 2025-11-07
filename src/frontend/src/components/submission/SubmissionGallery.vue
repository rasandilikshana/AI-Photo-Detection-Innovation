<template>
  <div class="submission-gallery">
    <!-- Loading State -->
    <LoadingSpinner
      v-if="submissionStore.loading"
      message="Loading submissions..."
    />

    <!-- Error State -->
    <ErrorMessage
      v-else-if="submissionStore.error"
      :message="submissionStore.error"
      @close="submissionStore.clearError()"
    />

    <!-- Empty State -->
    <v-card v-else-if="submissions.length === 0" elevation="0" class="text-center pa-8">
      <v-icon size="64" color="grey" class="mb-4">mdi-image-off</v-icon>
      <h3 class="text-h6 font-weight-bold mb-2">No Submissions Yet</h3>
      <p class="text-body-2 text-medium-emphasis">
        Be the first to submit to this competition!
      </p>
    </v-card>

    <!-- Gallery Grid -->
    <v-row v-else>
      <v-col
        v-for="submission in submissions"
        :key="submission.id"
        cols="12"
        sm="6"
        md="4"
        lg="3"
      >
        <v-card
          :to="{ name: 'submission-detail', params: { id: submission.id } }"
          elevation="2"
          hover
          class="submission-card"
        >
          <!-- Image -->
          <v-img
            :src="submission.thumbnail_url || submission.image_url"
            :alt="submission.title"
            aspect-ratio="1"
            cover
            class="submission-image"
          >
            <!-- AI Detection Badge -->
            <div class="pa-2 d-flex justify-end">
              <v-chip
                v-if="submission.ai_detection_status === 'authentic'"
                color="success"
                size="small"
                variant="flat"
              >
                <v-icon start size="small">mdi-shield-check</v-icon>
                Verified
              </v-chip>
              <v-chip
                v-else-if="submission.ai_detection_status === 'suspicious'"
                color="warning"
                size="small"
                variant="flat"
              >
                <v-icon start size="small">mdi-alert</v-icon>
                Under Review
              </v-chip>
            </div>

            <!-- Rank Badge (if ranked) -->
            <div v-if="submission.rank" class="rank-badge">
              <v-chip
                :color="getRankColor(submission.rank)"
                size="large"
                variant="flat"
              >
                <v-icon start>{{ getRankIcon(submission.rank) }}</v-icon>
                #{{ submission.rank }}
              </v-chip>
            </div>
          </v-img>

          <v-card-text class="pb-2">
            <!-- Title -->
            <h4 class="text-subtitle-1 font-weight-bold mb-1 text-truncate">
              {{ submission.title }}
            </h4>

            <!-- Description -->
            <p
              v-if="submission.description"
              class="text-caption text-medium-emphasis line-clamp-2 mb-2"
            >
              {{ submission.description }}
            </p>

            <!-- Score (if available) -->
            <div v-if="submission.score !== null && submission.score !== undefined" class="mb-2">
              <v-chip size="small" variant="outlined">
                <v-icon start size="small">mdi-star</v-icon>
                {{ submission.score.toFixed(1) }} / 10
              </v-chip>
            </div>

            <!-- Metadata -->
            <div class="d-flex align-center text-caption text-medium-emphasis">
              <v-icon size="small" class="mr-1">mdi-calendar</v-icon>
              {{ formatDate(submission.submitted_at) }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Load More -->
    <div v-if="hasMore && submissions.length > 0" class="text-center mt-6">
      <v-btn
        color="primary"
        :loading="submissionStore.loading"
        @click="emit('load-more')"
      >
        Load More Submissions
      </v-btn>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { format } from 'date-fns'
import { useSubmissionStore } from '@/store/submission'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorMessage from '@/components/common/ErrorMessage.vue'
import type { Submission } from '@/types/submission.types'

interface Props {
  submissions: Submission[]
  hasMore?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'load-more': []
}>()

const submissionStore = useSubmissionStore()

function formatDate(dateString: string): string {
  return format(new Date(dateString), 'MMM dd, yyyy')
}

function getRankColor(rank: number): string {
  if (rank === 1) return 'yellow-darken-2'
  if (rank === 2) return 'grey-lighten-1'
  if (rank === 3) return 'deep-orange-darken-1'
  return 'primary'
}

function getRankIcon(rank: number): string {
  if (rank === 1) return 'mdi-trophy'
  if (rank === 2) return 'mdi-medal'
  if (rank === 3) return 'mdi-medal-outline'
  return 'mdi-numeric-' + rank + '-circle'
}
</script>

<style scoped>
.submission-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease-in-out;
}

.submission-card:hover {
  transform: translateY(-4px);
}

.submission-image {
  position: relative;
}

.rank-badge {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
