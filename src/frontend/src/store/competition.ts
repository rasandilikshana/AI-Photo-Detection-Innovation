/**
 * Competition Store
 * Manages competition data and operations
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { competitionService } from '@/services/competition.service'
import type {
  Competition,
  CompetitionCreateRequest,
  CompetitionUpdateRequest,
  CompetitionFilters,
} from '@/types/competition.types'
import { handleApiError } from '@/services/api'

export const useCompetitionStore = defineStore('competition', () => {
  // State
  const competitions = ref<Competition[]>([])
  const currentCompetition = ref<Competition | null>(null)
  const myCompetitions = ref<Competition[]>([])
  const filters = ref<CompetitionFilters>({
    skip: 0,
    limit: 20,
  })
  const loading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)

  // Getters
  const hasMore = computed(() => competitions.value.length < total.value)
  const activeCompetitions = computed(() =>
    competitions.value.filter((c) => c.status === 'open')
  )
  const upcomingCompetitions = computed(() =>
    competitions.value.filter((c) => c.status === 'draft')
  )
  const completedCompetitions = computed(() =>
    competitions.value.filter((c) => c.status === 'completed')
  )

  // Actions

  /**
   * Fetch competitions with filters
   */
  async function fetchCompetitions(newFilters?: CompetitionFilters): Promise<void> {
    loading.value = true
    error.value = null

    try {
      if (newFilters) {
        filters.value = { ...filters.value, ...newFilters }
      }

      const data = await competitionService.getCompetitions(filters.value)
      competitions.value = data
      total.value = data.length // In real implementation, this would come from API
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Load more competitions (pagination)
   */
  async function loadMore(): Promise<void> {
    if (!hasMore.value || loading.value) return

    const currentSkip = filters.value.skip || 0
    const currentLimit = filters.value.limit || 20

    loading.value = true
    error.value = null

    try {
      const newFilters = {
        ...filters.value,
        skip: currentSkip + currentLimit,
      }

      const data = await competitionService.getCompetitions(newFilters)

      if (data.length > 0) {
        competitions.value = [...competitions.value, ...data]
        filters.value = newFilters
      }
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch single competition by ID
   */
  async function fetchCompetition(id: number): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const data = await competitionService.getCompetition(id)
      currentCompetition.value = data

      // Update in list if exists
      const index = competitions.value.findIndex((c) => c.id === id)
      if (index !== -1) {
        competitions.value[index] = data
      }
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch competition by slug
   */
  async function fetchCompetitionBySlug(slug: string): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const data = await competitionService.getCompetitionBySlug(slug)
      currentCompetition.value = data
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Create new competition (organizer)
   */
  async function createCompetition(data: CompetitionCreateRequest): Promise<Competition> {
    loading.value = true
    error.value = null

    try {
      const newCompetition = await competitionService.createCompetition(data)

      // Add to lists
      competitions.value.unshift(newCompetition)
      myCompetitions.value.unshift(newCompetition)

      return newCompetition
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Update competition (organizer)
   */
  async function updateCompetition(id: number, data: CompetitionUpdateRequest): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const updated = await competitionService.updateCompetition(id, data)

      // Update in all lists
      const updateInList = (list: Competition[]) => {
        const index = list.findIndex((c) => c.id === id)
        if (index !== -1) {
          list[index] = updated
        }
      }

      updateInList(competitions.value)
      updateInList(myCompetitions.value)

      if (currentCompetition.value?.id === id) {
        currentCompetition.value = updated
      }
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete competition (organizer)
   */
  async function deleteCompetition(id: number): Promise<void> {
    loading.value = true
    error.value = null

    try {
      await competitionService.deleteCompetition(id)

      // Remove from all lists
      competitions.value = competitions.value.filter((c) => c.id !== id)
      myCompetitions.value = myCompetitions.value.filter((c) => c.id !== id)

      if (currentCompetition.value?.id === id) {
        currentCompetition.value = null
      }
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch user's competitions (organizer)
   */
  async function fetchMyCompetitions(): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const data = await competitionService.getMyCompetitions()
      myCompetitions.value = data
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Upload cover image
   */
  async function uploadCoverImage(competitionId: number, file: File): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const result = await competitionService.uploadCoverImage(competitionId, file)

      // Update competition with new cover image URL
      const updateCoverImage = (list: Competition[]) => {
        const competition = list.find((c) => c.id === competitionId)
        if (competition) {
          competition.cover_image_url = result.cover_image_url
        }
      }

      updateCoverImage(competitions.value)
      updateCoverImage(myCompetitions.value)

      if (currentCompetition.value?.id === competitionId) {
        currentCompetition.value.cover_image_url = result.cover_image_url
      }
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear current competition
   */
  function clearCurrent() {
    currentCompetition.value = null
  }

  /**
   * Clear error
   */
  function clearError() {
    error.value = null
  }

  /**
   * Reset filters
   */
  function resetFilters() {
    filters.value = {
      skip: 0,
      limit: 20,
    }
  }

  return {
    // State
    competitions,
    currentCompetition,
    myCompetitions,
    filters,
    loading,
    error,
    total,
    // Getters
    hasMore,
    activeCompetitions,
    upcomingCompetitions,
    completedCompetitions,
    // Actions
    fetchCompetitions,
    loadMore,
    fetchCompetition,
    fetchCompetitionBySlug,
    createCompetition,
    updateCompetition,
    deleteCompetition,
    fetchMyCompetitions,
    uploadCoverImage,
    clearCurrent,
    clearError,
    resetFilters,
  }
})
