/**
 * Submission Types
 */

export interface Submission {
  id: number
  competition_id: number
  user_id: number
  title: string
  description?: string
  image_url: string
  raw_file_url?: string
  thumbnail_url?: string
  camera_model?: string
  lens_model?: string
  focal_length?: string
  aperture?: string
  shutter_speed?: string
  iso?: string
  capture_date?: string
  location?: string
  ai_detection_score?: number
  ai_detection_status: AIDetectionStatus
  linkage_verified: boolean
  status: SubmissionStatus
  score?: number
  rank?: number
  submitted_at: string
  created_at: string
  updated_at: string
}

export type SubmissionStatus = 'draft' | 'submitted' | 'under_review' | 'approved' | 'rejected' | 'disqualified'

export type AIDetectionStatus = 'pending' | 'processing' | 'authentic' | 'suspicious' | 'ai_generated' | 'failed'

export interface SubmissionCreateRequest {
  competition_id: number
  title: string
  description?: string
  camera_model?: string
  lens_model?: string
  focal_length?: string
  aperture?: string
  shutter_speed?: string
  iso?: string
  capture_date?: string
  location?: string
}

export interface SubmissionUpdateRequest {
  title?: string
  description?: string
  camera_model?: string
  lens_model?: string
  focal_length?: string
  aperture?: string
  shutter_speed?: string
  iso?: string
  capture_date?: string
  location?: string
}

export interface SubmissionFilters {
  competition_id?: number
  status?: SubmissionStatus
  ai_detection_status?: AIDetectionStatus
  skip?: number
  limit?: number
}

export interface SubmissionState {
  submissions: Submission[]
  currentSubmission: Submission | null
  uploadProgress: number
  loading: boolean
  total: number
}

export interface FileUploadProgress {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'completed' | 'error'
  error?: string
}
