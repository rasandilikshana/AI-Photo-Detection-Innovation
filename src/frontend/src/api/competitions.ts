import client from './client'
import type { Competition, CompetitionCreate, CompetitionUpdate } from '@/types'

export const competitionsApi = {
  async getAll(params?: { skip?: number; limit?: number; status?: string }): Promise<Competition[]> {
    const response = await client.get('/competitions', { params })
    return response.data
  },

  async getById(id: number): Promise<Competition> {
    const response = await client.get(`/competitions/${id}`)
    return response.data
  },

  async getBySlug(slug: string): Promise<Competition> {
    const response = await client.get(`/competitions/slug/${slug}`)
    return response.data
  },

  async create(data: CompetitionCreate): Promise<Competition> {
    const response = await client.post('/competitions', data)
    return response.data
  },

  async update(id: number, data: CompetitionUpdate): Promise<Competition> {
    const response = await client.patch(`/competitions/${id}`, data)
    return response.data
  },

  async delete(id: number): Promise<void> {
    await client.delete(`/competitions/${id}`)
  },
}
