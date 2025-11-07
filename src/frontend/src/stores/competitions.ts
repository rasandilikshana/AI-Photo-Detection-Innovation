import { defineStore } from 'pinia'
import { ref } from 'vue'
import { competitionsApi } from '@/api'
import type { Competition, CompetitionCreate, CompetitionUpdate } from '@/types'

export const useCompetitionsStore = defineStore('competitions', () => {
  const competitions = ref<Competition[]>([])
  const currentCompetition = ref<Competition | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchCompetitions(params?: { skip?: number; limit?: number; status?: string }) {
    isLoading.value = true
    error.value = null
    try {
      competitions.value = await competitionsApi.getAll(params)
      return competitions.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch competitions'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCompetitionById(id: number) {
    isLoading.value = true
    error.value = null
    try {
      currentCompetition.value = await competitionsApi.getById(id)
      return currentCompetition.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch competition'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCompetitionBySlug(slug: string) {
    isLoading.value = true
    error.value = null
    try {
      currentCompetition.value = await competitionsApi.getBySlug(slug)
      return currentCompetition.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch competition'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createCompetition(data: CompetitionCreate) {
    isLoading.value = true
    error.value = null
    try {
      const newCompetition = await competitionsApi.create(data)
      competitions.value.unshift(newCompetition)
      return newCompetition
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to create competition'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateCompetition(id: number, data: CompetitionUpdate) {
    isLoading.value = true
    error.value = null
    try {
      const updated = await competitionsApi.update(id, data)
      const index = competitions.value.findIndex(c => c.id === id)
      if (index !== -1) {
        competitions.value[index] = updated
      }
      if (currentCompetition.value?.id === id) {
        currentCompetition.value = updated
      }
      return updated
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to update competition'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteCompetition(id: number) {
    isLoading.value = true
    error.value = null
    try {
      await competitionsApi.delete(id)
      competitions.value = competitions.value.filter(c => c.id !== id)
      if (currentCompetition.value?.id === id) {
        currentCompetition.value = null
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to delete competition'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    competitions,
    currentCompetition,
    isLoading,
    error,
    fetchCompetitions,
    fetchCompetitionById,
    fetchCompetitionBySlug,
    createCompetition,
    updateCompetition,
    deleteCompetition,
    clearError,
  }
})
