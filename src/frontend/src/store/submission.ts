/**
 * Submission Store
 * Manages submission data and operations
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { submissionService } from '@/services/submission.service'
import type {
  Submission,
  SubmissionCreateRequest,
  SubmissionUpdateRequest,
  SubmissionFilters,
  FileUploadProgress,
} from '@/types/submission.types'
import { handleApiError } from '@/services/api'

export const useSubmissionStore = defineStore('submission', () => {
  // State
  const submissions = ref<Submission[]>([])
  const currentSubmission = ref<Submission | null>(null)
  const mySubmissions = ref<Submission[]>([])
  const uploadProgress = ref(0)
  const uploadingFiles = ref<FileUploadProgress[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)

  // Getters
  const draftSubmissions = computed(() =>
    mySubmissions.value.filter((s) => s.status === 'draft')
  )
  const submittedSubmissions = computed(() =>
    mySubmissions.value.filter((s) => s.status === 'submitted' || s.status === 'under_review')
  )
  const approvedSubmissions = computed(() =>
    mySubmissions.value.filter((s) => s.status === 'approved')
  )
  const isUploading = computed(() => uploadProgress.value > 0 && uploadProgress.value < 100)

  // Actions

  /**
   * Fetch submissions with filters
   */
  async function fetchSubmissions(filters?: SubmissionFilters): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const data = await submissionService.getSubmissions(filters)
      submissions.value = data
      total.value = data.length
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch single submission by ID
   */
  async function fetchSubmission(id: number): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const data = await submissionService.getSubmission(id)
      currentSubmission.value = data

      // Update in list if exists
      const index = submissions.value.findIndex((s) => s.id === id)
      if (index !== -1) {
        submissions.value[index] = data
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
   * Create new submission
   */
  async function createSubmission(data: SubmissionCreateRequest): Promise<Submission> {
    loading.value = true
    error.value = null

    try {
      const newSubmission = await submissionService.createSubmission(data)

      // Add to lists
      submissions.value.unshift(newSubmission)
      mySubmissions.value.unshift(newSubmission)
      currentSubmission.value = newSubmission

      return newSubmission
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Update submission
   */
  async function updateSubmission(id: number, data: SubmissionUpdateRequest): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const updated = await submissionService.updateSubmission(id, data)

      // Update in all lists
      const updateInList = (list: Submission[]) => {
        const index = list.findIndex((s) => s.id === id)
        if (index !== -1) {
          list[index] = updated
        }
      }

      updateInList(submissions.value)
      updateInList(mySubmissions.value)

      if (currentSubmission.value?.id === id) {
        currentSubmission.value = updated
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
   * Delete submission
   */
  async function deleteSubmission(id: number): Promise<void> {
    loading.value = true
    error.value = null

    try {
      await submissionService.deleteSubmission(id)

      // Remove from all lists
      submissions.value = submissions.value.filter((s) => s.id !== id)
      mySubmissions.value = mySubmissions.value.filter((s) => s.id !== id)

      if (currentSubmission.value?.id === id) {
        currentSubmission.value = null
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
   * Upload submission image
   */
  async function uploadImage(submissionId: number, file: File): Promise<void> {
    uploadProgress.value = 0
    error.value = null

    try {
      const result = await submissionService.uploadImage(submissionId, file, (progress) => {
        uploadProgress.value = progress
      })

      // Update submission with new image URLs
      const updateImage = (list: Submission[]) => {
        const submission = list.find((s) => s.id === submissionId)
        if (submission) {
          submission.image_url = result.image_url
          if (result.thumbnail_url) {
            submission.thumbnail_url = result.thumbnail_url
          }
        }
      }

      updateImage(submissions.value)
      updateImage(mySubmissions.value)

      if (currentSubmission.value?.id === submissionId) {
        currentSubmission.value.image_url = result.image_url
        if (result.thumbnail_url) {
          currentSubmission.value.thumbnail_url = result.thumbnail_url
        }
      }

      uploadProgress.value = 100
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      uploadProgress.value = 0
      throw err
    }
  }

  /**
   * Upload raw file
   */
  async function uploadRawFile(submissionId: number, file: File): Promise<void> {
    uploadProgress.value = 0
    error.value = null

    try {
      const result = await submissionService.uploadRawFile(submissionId, file, (progress) => {
        uploadProgress.value = progress
      })

      // Update submission with raw file URL
      const updateRawFile = (list: Submission[]) => {
        const submission = list.find((s) => s.id === submissionId)
        if (submission) {
          submission.raw_file_url = result.raw_file_url
        }
      }

      updateRawFile(submissions.value)
      updateRawFile(mySubmissions.value)

      if (currentSubmission.value?.id === submissionId) {
        currentSubmission.value.raw_file_url = result.raw_file_url
      }

      uploadProgress.value = 100
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      uploadProgress.value = 0
      throw err
    }
  }

  /**
   * Submit for review
   */
  async function submitForReview(id: number): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const updated = await submissionService.submitForReview(id)

      // Update in all lists
      const updateInList = (list: Submission[]) => {
        const index = list.findIndex((s) => s.id === id)
        if (index !== -1) {
          list[index] = updated
        }
      }

      updateInList(submissions.value)
      updateInList(mySubmissions.value)

      if (currentSubmission.value?.id === id) {
        currentSubmission.value = updated
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
   * Fetch user's submissions
   */
  async function fetchMySubmissions(competitionId?: number): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const data = await submissionService.getMySubmissions(competitionId)
      mySubmissions.value = data
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch competition submissions (public)
   */
  async function fetchCompetitionSubmissions(competitionId: number): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const data = await submissionService.getCompetitionSubmissions(competitionId)
      submissions.value = data
      total.value = data.length
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear current submission
   */
  function clearCurrent() {
    currentSubmission.value = null
    uploadProgress.value = 0
  }

  /**
   * Clear error
   */
  function clearError() {
    error.value = null
  }

  /**
   * Reset upload progress
   */
  function resetUploadProgress() {
    uploadProgress.value = 0
  }

  return {
    // State
    submissions,
    currentSubmission,
    mySubmissions,
    uploadProgress,
    uploadingFiles,
    loading,
    error,
    total,
    // Getters
    draftSubmissions,
    submittedSubmissions,
    approvedSubmissions,
    isUploading,
    // Actions
    fetchSubmissions,
    fetchSubmission,
    createSubmission,
    updateSubmission,
    deleteSubmission,
    uploadImage,
    uploadRawFile,
    submitForReview,
    fetchMySubmissions,
    fetchCompetitionSubmissions,
    clearCurrent,
    clearError,
    resetUploadProgress,
  }
})
