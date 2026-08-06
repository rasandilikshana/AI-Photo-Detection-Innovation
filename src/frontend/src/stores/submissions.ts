import { defineStore } from 'pinia'
import { ref } from 'vue'
import { submissionsApi } from '@/api'
import type { Submission, SubmissionCreate } from '@/types'

export const useSubmissionsStore = defineStore('submissions', () => {
  const submissions = ref<Submission[]>([])
  const currentSubmission = ref<Submission | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchSubmissions(params?: { competition_id?: number; user_id?: number; skip?: number; limit?: number }) {
    isLoading.value = true
    error.value = null
    try {
      submissions.value = await submissionsApi.getAll(params)
      return submissions.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch submissions'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchSubmissionById(id: number) {
    isLoading.value = true
    error.value = null
    try {
      currentSubmission.value = await submissionsApi.getById(id)
      return currentSubmission.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch submission'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createSubmission(data: SubmissionCreate, onProgress?: (percent: number) => void) {
    isLoading.value = true
    error.value = null
    try {
      const newSubmission = await submissionsApi.create(data, onProgress)
      submissions.value.unshift(newSubmission)
      return newSubmission
    } catch (err: any) {
      if (err.code === 'ECONNABORTED') {
        error.value = 'Upload timed out. Please check your internet connection and try again.'
      } else {
        error.value = err.response?.data?.detail || 'Failed to create submission'
      }
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteSubmission(id: number) {
    isLoading.value = true
    error.value = null
    try {
      await submissionsApi.delete(id)
      submissions.value = submissions.value.filter(s => s.id !== id)
      if (currentSubmission.value?.id === id) {
        currentSubmission.value = null
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to delete submission'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    submissions,
    currentSubmission,
    isLoading,
    error,
    fetchSubmissions,
    fetchSubmissionById,
    createSubmission,
    deleteSubmission,
    clearError,
  }
})
