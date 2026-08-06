import client from './client'
import type { Submission, SubmissionCreate } from '@/types'

export const submissionsApi = {
  async getAll(params?: { competition_id?: number; user_id?: number; skip?: number; limit?: number }): Promise<Submission[]> {
    const response = await client.get('/submissions', { params })
    return response.data
  },

  async getById(id: number): Promise<Submission> {
    const response = await client.get(`/submissions/${id}`)
    return response.data
  },

  async create(data: SubmissionCreate, onProgress?: (percent: number) => void): Promise<Submission> {
    const formData = new FormData()
    formData.append('title', data.title)
    formData.append('competition_id', data.competition_id.toString())
    if (data.description) {
      formData.append('description', data.description)
    }
    formData.append('jpg_file', data.jpg_file)
    if (data.raw_file) {
      formData.append('raw_file', data.raw_file)
    }

    const response = await client.post('/submissions', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      // Large JPG+RAW uploads can take minutes on slow uplinks — the global
      // 30s timeout kills them mid-transfer, so give uploads their own budget
      timeout: 600000, // 10 minutes
      onUploadProgress: (event) => {
        if (onProgress && event.total) {
          onProgress(Math.round((event.loaded / event.total) * 100))
        }
      },
    })
    return response.data
  },

  async delete(id: number): Promise<void> {
    await client.delete(`/submissions/${id}`)
  },
}
