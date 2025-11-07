<template>
  <v-container class="py-8">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <h1 class="text-h3 font-weight-bold mb-2">Photography Competitions</h1>
        <p class="text-h6 text-medium-emphasis mb-6">
          Discover and participate in authentic photography competitions
        </p>
      </v-col>
    </v-row>

    <!-- Filters -->
    <CompetitionFilters
      v-model="filters"
      :view-mode="viewMode"
      @sort-change="handleSortChange"
      @view-mode-change="viewMode = $event"
    />

    <!-- Loading State -->
    <LoadingSpinner
      v-if="competitionStore.loading && competitions.length === 0"
      message="Loading competitions..."
    />

    <!-- Error State -->
    <ErrorMessage
      v-else-if="competitionStore.error"
      :message="competitionStore.error"
      title="Failed to load competitions"
      @close="competitionStore.clearError()"
    />

    <!-- Empty State -->
    <v-row v-else-if="competitions.length === 0 && !competitionStore.loading">
      <v-col cols="12">
        <v-card elevation="2" class="pa-8 text-center">
          <v-icon size="80" color="grey" class="mb-4">
            mdi-trophy-outline
          </v-icon>
          <h3 class="text-h5 font-weight-bold mb-2">No Competitions Found</h3>
          <p class="text-body-1 text-medium-emphasis mb-6">
            {{ hasActiveFilters ? 'Try adjusting your filters' : 'Check back later for new competitions' }}
          </p>
          <v-btn
            v-if="hasActiveFilters"
            color="primary"
            @click="clearFilters"
          >
            Clear Filters
          </v-btn>
        </v-card>
      </v-col>
    </v-row>

    <!-- Grid View -->
    <v-row v-else-if="viewMode === 'grid'">
      <v-col
        v-for="competition in competitions"
        :key="competition.id"
        cols="12"
        sm="6"
        md="4"
        lg="3"
      >
        <CompetitionCard :competition="competition" />
      </v-col>
    </v-row>

    <!-- List View -->
    <v-row v-else>
      <v-col
        v-for="competition in competitions"
        :key="competition.id"
        cols="12"
      >
        <CompetitionCard :competition="competition" />
      </v-col>
    </v-row>

    <!-- Load More / Pagination -->
    <v-row v-if="competitions.length > 0" class="mt-6">
      <v-col cols="12" class="text-center">
        <v-btn
          v-if="competitionStore.hasMore"
          color="primary"
          size="large"
          :loading="competitionStore.loading"
          @click="loadMore"
        >
          Load More
        </v-btn>
        <p v-else class="text-body-2 text-medium-emphasis">
          Showing all {{ competitions.length }} competition{{ competitions.length !== 1 ? 's' : '' }}
        </p>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useCompetitionStore } from '@/store/competition'
import { useToast } from 'vue-toastification'
import CompetitionCard from '@/components/competition/CompetitionCard.vue'
import CompetitionFilters from '@/components/competition/CompetitionFilters.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorMessage from '@/components/common/ErrorMessage.vue'
import type { CompetitionFilters as ICompetitionFilters } from '@/types/competition.types'

const competitionStore = useCompetitionStore()
const toast = useToast()

const viewMode = ref<'grid' | 'list'>('grid')
const sortBy = ref('newest')

const filters = ref<ICompetitionFilters>({
  skip: 0,
  limit: 20,
})

const competitions = computed(() => competitionStore.competitions)

const hasActiveFilters = computed(() => {
  return !!(filters.value.search || filters.value.status)
})

// Load competitions on mount
onMounted(async () => {
  await fetchCompetitions()
})

// Watch filters and refetch
watch(
  filters,
  async (newFilters) => {
    await fetchCompetitions(newFilters)
  },
  { deep: true }
)

async function fetchCompetitions(customFilters?: ICompetitionFilters) {
  try {
    await competitionStore.fetchCompetitions(customFilters || filters.value)
  } catch (error) {
    toast.error('Failed to load competitions')
  }
}

async function loadMore() {
  try {
    await competitionStore.loadMore()
  } catch (error) {
    toast.error('Failed to load more competitions')
  }
}

function handleSortChange(sort: string) {
  sortBy.value = sort
  // In a real implementation, this would trigger API call with sort parameter
  // For now, we'll just store the sort preference
  toast.info(`Sorting by: ${sort}`)
}

function clearFilters() {
  filters.value = {
    skip: 0,
    limit: 20,
  }
}
</script>
