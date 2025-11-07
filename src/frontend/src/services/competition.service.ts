/**
 * Competition API Service
 */

import api from './api'
import type {
  Competition,
  CompetitionCreateRequest,
  CompetitionUpdateRequest,
  CompetitionFilters,
} from '@/types/competition.types'

export const competitionService = {
  /**
   * Get all competitions with filters
   */
  async getCompetitions(filters?: CompetitionFilters): Promise<Competition[]> {
    const params = new URLSearchParams()

    if (filters?.status) params.append('status', filters.status)
    if (filters?.search) params.append('search', filters.search)
    if (filters?.skip !== undefined) params.append('skip', filters.skip.toString())
    if (filters?.limit !== undefined) params.append('limit', filters.limit.toString())

    const response = await api.get<Competition[]>(`/competitions?${params.toString()}`)
    return response.data
  },

  /**
   * Get competition by ID
   */
  async getCompetition(id: number): Promise<Competition> {
    const response = await api.get<Competition>(`/competitions/${id}`)
    return response.data
  },

  /**
   * Get competition by slug
   */
  async getCompetitionBySlug(slug: string): Promise<Competition> {
    const response = await api.get<Competition>(`/competitions/slug/${slug}`)
    return response.data
  },

  /**
   * Create new competition (organizer only)
   */
  async createCompetition(data: CompetitionCreateRequest): Promise<Competition> {
    const response = await api.post<Competition>('/competitions', data)
    return response.data
  },

  /**
   * Update competition (organizer only)
   */
  async updateCompetition(id: number, data: CompetitionUpdateRequest): Promise<Competition> {
    const response = await api.put<Competition>(`/competitions/${id}`, data)
    return response.data
  },

  /**
   * Delete competition (organizer only)
   */
  async deleteCompetition(id: number): Promise<void> {
    await api.delete(`/competitions/${id}`)
  },

  /**
   * Get competitions created by current user (organizer)
   */
  async getMyCompetitions(): Promise<Competition[]> {
    const response = await api.get<Competition[]>('/competitions/my')
    return response.data
  },

  /**
   * Get active/open competitions
   */
  async getActiveCompetitions(): Promise<Competition[]> {
    return this.getCompetitions({ status: 'open' })
  },

  /**
   * Upload competition cover image
   */
  async uploadCoverImage(competitionId: number, file: File): Promise<{ cover_image_url: string }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post<{ cover_image_url: string }>(
      `/competitions/${competitionId}/cover-image`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },
}

export default competitionService
