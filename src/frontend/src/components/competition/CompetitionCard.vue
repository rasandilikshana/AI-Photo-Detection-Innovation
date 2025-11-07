<template>
  <v-card
    class="competition-card"
    :to="{ name: 'competition-detail', params: { slug: competition.slug } }"
    elevation="2"
    hover
  >
    <!-- Cover Image -->
    <v-img
      :src="coverImage"
      :alt="competition.title"
      height="200"
      cover
      class="competition-cover"
    >
      <!-- Status Badge -->
      <div class="pa-3 d-flex justify-space-between align-start">
        <v-chip
          :color="statusColor"
          size="small"
          variant="flat"
          class="text-uppercase font-weight-bold"
        >
          {{ competition.status }}
        </v-chip>

        <!-- Prize Badge -->
        <v-chip
          v-if="competition.prize_amount"
          color="success"
          size="small"
          variant="flat"
        >
          <v-icon start size="small">mdi-currency-usd</v-icon>
          {{ formatPrize(competition.prize_amount) }}
        </v-chip>
      </div>
    </v-img>

    <v-card-text class="pb-2">
      <!-- Title -->
      <h3 class="text-h6 font-weight-bold mb-2 text-truncate">
        {{ competition.title }}
      </h3>

      <!-- Description -->
      <p
        v-if="competition.description"
        class="text-body-2 text-medium-emphasis mb-3 line-clamp-2"
      >
        {{ competition.description }}
      </p>

      <!-- Dates -->
      <div class="mb-3">
        <div class="d-flex align-center mb-1">
          <v-icon size="small" color="primary" class="mr-2">
            mdi-calendar-start
          </v-icon>
          <span class="text-caption">
            <strong>Starts:</strong> {{ formatDate(competition.submission_start) }}
          </span>
        </div>
        <div class="d-flex align-center">
          <v-icon size="small" color="error" class="mr-2">
            mdi-calendar-end
          </v-icon>
          <span class="text-caption">
            <strong>Ends:</strong> {{ formatDate(competition.submission_end) }}
          </span>
        </div>
      </div>

      <!-- Stats -->
      <v-divider class="mb-3" />
      <div class="d-flex justify-space-between text-caption">
        <div class="d-flex align-center">
          <v-icon size="small" class="mr-1">mdi-image-multiple</v-icon>
          {{ competition.total_submissions }} submissions
        </div>
        <div class="d-flex align-center">
          <v-icon size="small" class="mr-1">mdi-account-group</v-icon>
          {{ competition.total_participants }} participants
        </div>
      </div>
    </v-card-text>

    <!-- Actions -->
    <v-card-actions class="pt-0">
      <v-btn
        color="primary"
        variant="text"
        block
      >
        View Details
        <v-icon end>mdi-arrow-right</v-icon>
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { format } from 'date-fns'
import type { Competition } from '@/types/competition.types'

interface Props {
  competition: Competition
}

const props = defineProps<Props>()

const coverImage = computed(() => {
  return props.competition.cover_image_url || 'https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=800'
})

const statusColor = computed(() => {
  switch (props.competition.status) {
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

function formatDate(dateString: string): string {
  return format(new Date(dateString), 'MMM dd, yyyy')
}

function formatPrize(amount: number): string {
  if (amount >= 1000) {
    return `$${(amount / 1000).toFixed(1)}k`
  }
  return `$${amount}`
}
</script>

<style scoped>
.competition-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease-in-out;
}

.competition-card:hover {
  transform: translateY(-4px);
}

.competition-cover {
  position: relative;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.5;
  max-height: 3em;
}
</style>
