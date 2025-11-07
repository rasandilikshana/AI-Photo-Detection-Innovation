<template>
  <v-card elevation="2" class="mb-6">
    <v-card-text>
      <v-row>
        <!-- Search -->
        <v-col cols="12" md="4">
          <v-text-field
            :model-value="modelValue.search"
            label="Search competitions"
            placeholder="Search competitions..."
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            density="comfortable"
            clearable
            hide-details
            @update:model-value="updateFilter('search', $event)"
          />
        </v-col>

        <!-- Status Filter -->
        <v-col cols="12" sm="6" md="3">
          <v-select
            :model-value="modelValue.status"
            :items="statusOptions"
            label="Status"
            prepend-inner-icon="mdi-filter"
            variant="outlined"
            density="comfortable"
            clearable
            hide-details
            @update:model-value="updateFilter('status', $event)"
          />
        </v-col>

        <!-- Sort By -->
        <v-col cols="12" sm="6" md="3">
          <v-select
            v-model="sortBy"
            :items="sortOptions"
            label="Sort by"
            prepend-inner-icon="mdi-sort"
            variant="outlined"
            density="comfortable"
            hide-details
            @update:model-value="emit('sort-change', $event)"
          />
        </v-col>

        <!-- View Toggle -->
        <v-col cols="12" md="2" class="d-flex align-center justify-end">
          <v-btn-toggle
            :model-value="viewMode"
            mandatory
            variant="outlined"
            divided
            @update:model-value="emit('view-mode-change', $event)"
          >
            <v-btn value="grid" icon size="small">
              <v-icon>mdi-view-grid</v-icon>
            </v-btn>
            <v-btn value="list" icon size="small">
              <v-icon>mdi-view-list</v-icon>
            </v-btn>
          </v-btn-toggle>
        </v-col>
      </v-row>

      <!-- Active Filters Display -->
      <v-row v-if="hasActiveFilters" class="mt-2">
        <v-col cols="12">
          <div class="d-flex align-center flex-wrap gap-2">
            <span class="text-caption text-medium-emphasis">Active filters:</span>

            <v-chip
              v-if="modelValue.search"
              size="small"
              closable
              @click:close="updateFilter('search', null)"
            >
              Search: {{ modelValue.search }}
            </v-chip>

            <v-chip
              v-if="modelValue.status"
              size="small"
              closable
              @click:close="updateFilter('status', null)"
            >
              Status: {{ modelValue.status }}
            </v-chip>

            <v-btn
              v-if="hasActiveFilters"
              size="small"
              variant="text"
              color="error"
              @click="clearAllFilters"
            >
              Clear All
            </v-btn>
          </div>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { CompetitionFilters } from '@/types/competition.types'

interface Props {
  modelValue: CompetitionFilters
  viewMode?: 'grid' | 'list'
}

const props = withDefaults(defineProps<Props>(), {
  viewMode: 'grid',
})

const emit = defineEmits<{
  'update:modelValue': [value: CompetitionFilters]
  'sort-change': [value: string]
  'view-mode-change': [value: 'grid' | 'list']
}>()

const sortBy = ref('newest')

const statusOptions = [
  { title: 'All Status', value: null },
  { title: 'Open', value: 'open' },
  { title: 'Draft', value: 'draft' },
  { title: 'Judging', value: 'judging' },
  { title: 'Completed', value: 'completed' },
  { title: 'Closed', value: 'closed' },
]

const sortOptions = [
  { title: 'Newest First', value: 'newest' },
  { title: 'Ending Soon', value: 'ending-soon' },
  { title: 'Most Popular', value: 'popular' },
  { title: 'Highest Prize', value: 'prize' },
]

const hasActiveFilters = computed(() => {
  return !!(props.modelValue.search || props.modelValue.status)
})

function updateFilter(key: keyof CompetitionFilters, value: any) {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: value,
  })
}

function clearAllFilters() {
  emit('update:modelValue', {
    skip: 0,
    limit: props.modelValue.limit || 20,
  })
}
</script>

<style scoped>
.gap-2 {
  gap: 0.5rem;
}
</style>
