/**
 * Submission API Service
 */

import api from './api'
import type {
  Submission,
  SubmissionCreateRequest,
  SubmissionUpdateRequest,
  SubmissionFilters,
} from '@/types/submission.types'

export const submissionService = {
  /**
   * Get submissions with filters
   */
  async getSubmissions(filters?: SubmissionFilters): Promise<Submission[]> {
    const params = new URLSearchParams()

    if (filters?.competition_id) params.append('competition_id', filters.competition_id.toString())
    if (filters?.status) params.append('status', filters.status)
    if (filters?.ai_detection_status) params.append('ai_detection_status', filters.ai_detection_status)
    if (filters?.skip !== undefined) params.append('skip', filters.skip.toString())
    if (filters?.limit !== undefined) params.append('limit', filters.limit.toString())

    const response = await api.get<Submission[]>(`/submissions?${params.toString()}`)
    return response.data
  },

  /**
   * Get submission by ID
   */
  async getSubmission(id: number): Promise<Submission> {
    const response = await api.get<Submission>(`/submissions/${id}`)
    return response.data
  },

  /**
   * Create new submission
   */
  async createSubmission(data: SubmissionCreateRequest): Promise<Submission> {
    const response = await api.post<Submission>('/submissions', data)
    return response.data
  },

  /**
   * Update submission
   */
  async updateSubmission(id: number, data: SubmissionUpdateRequest): Promise<Submission> {
    const response = await api.put<Submission>(`/submissions/${id}`, data)
    return response.data
  },

  /**
   * Delete submission
   */
  async deleteSubmission(id: number): Promise<void> {
    await api.delete(`/submissions/${id}`)
  },

  /**
   * Upload submission image
   */
  async uploadImage(
    submissionId: number,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<{ image_url: string; thumbnail_url?: string }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post<{ image_url: string; thumbnail_url?: string }>(
      `/submissions/${submissionId}/image`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(percentCompleted)
          }
        },
      }
    )
    return response.data
  },

  /**
   * Upload raw file (if required by competition)
   */
  async uploadRawFile(
    submissionId: number,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<{ raw_file_url: string }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post<{ raw_file_url: string }>(
      `/submissions/${submissionId}/raw-file`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(percentCompleted)
          }
        },
      }
    )
    return response.data
  },

  /**
   * Submit submission for review
   */
  async submitForReview(id: number): Promise<Submission> {
    const response = await api.post<Submission>(`/submissions/${id}/submit`)
    return response.data
  },

  /**
   * Get current user's submissions
   */
  async getMySubmissions(competitionId?: number): Promise<Submission[]> {
    const filters: SubmissionFilters = {}
    if (competitionId) filters.competition_id = competitionId

    return this.getSubmissions(filters)
  },

  /**
   * Get submissions for a competition (public)
   */
  async getCompetitionSubmissions(competitionId: number): Promise<Submission[]> {
    return this.getSubmissions({
      competition_id: competitionId,
      status: 'approved', // Only show approved submissions publicly
    })
  },
}

export default submissionService
