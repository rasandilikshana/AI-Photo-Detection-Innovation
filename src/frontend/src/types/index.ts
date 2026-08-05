// User Types
export interface User {
  id: number
  email: string
  username: string
  full_name?: string
  phone?: string
  country?: string
  bio?: string
  avatar_url?: string
  role: 'participant' | 'judge' | 'organizer' | 'admin'
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
}

export interface UserRegister {
  email: string
  username: string
  password: string
  full_name?: string
  phone?: string
  country?: string
}

export interface UserLogin {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

// Competition Types
export interface Competition {
  id: number
  title: string
  description: string
  rules?: string
  slug: string
  submission_start: string
  submission_end: string
  judging_start?: string
  judging_end?: string
  results_date?: string
  status: 'draft' | 'open' | 'closed' | 'judging' | 'completed' | 'cancelled'
  max_submissions_per_user: number
  require_raw_files: boolean
  allow_ai_generated: boolean
  entry_fee: number
  banner_url?: string
  thumbnail_url?: string
  prize_description?: string
  prize_amount?: number
  organizer_id: number
  organizer?: User
  created_at: string
  updated_at: string
  is_accepting_submissions?: boolean
  is_in_judging_phase?: boolean
}

export interface CompetitionCreate {
  title: string
  description: string
  rules?: string
  submission_start: string
  submission_end: string
  max_submissions_per_user?: number
  require_raw_files?: boolean
  allow_ai_generated?: boolean
  entry_fee?: number
  prize_description?: string
  prize_amount?: number
}

export interface CompetitionUpdate {
  title?: string
  description?: string
  rules?: string
  status?: Competition['status']
  submission_start?: string
  submission_end?: string
  judging_start?: string
  judging_end?: string
  results_date?: string
  max_submissions_per_user?: number
  require_raw_files?: boolean
  allow_ai_generated?: boolean
  entry_fee?: number
  prize_description?: string
  prize_amount?: number
}

// Submission Types
export interface Submission {
  id: number
  title: string
  description?: string
  jpg_file_url: string
  jpg_file_size: number
  raw_file_url?: string
  raw_file_size?: number
  status: 'pending' | 'analyzing' | 'approved' | 'rejected' | 'disqualified'
  verification_verdict?: 'authentic' | 'suspicious' | 'ai_generated' | 'needs_review'
  verification_confidence?: number
  verification_details?: Record<string, any>
  verification_timestamp?: string
  camera_make?: string
  camera_model?: string
  lens_model?: string
  iso?: number
  aperture?: string
  shutter_speed?: string
  capture_date?: string
  total_score: number
  score_count: number
  average_score?: number
  // Analysis error (when AI analysis fails)
  analysis_error?: string
  // Review/Rejection info (when judge manually reviews)
  rejection_reason?: string
  reviewed_by?: number
  reviewed_at?: string
  // V2.0 Camera Reputation fields
  camera_trust_score?: number
  prnu_fingerprint_id?: number
  prnu_extracted_energy?: number
  user_id: number
  competition_id: number
  user?: User
  competition?: Competition
  created_at: string
  updated_at: string
}

export interface SubmissionCreate {
  title: string
  competition_id: number
  description?: string
  jpg_file: File
  raw_file?: File
}

// Score Types
export interface Score {
  id: number
  composition_score: number
  technical_score: number
  creativity_score: number
  overall_score: number
  comments?: string
  submission_id: number
  judge_id: number
  judge?: User
  created_at: string
  updated_at: string
}

// API Response Types
export interface MessageResponse {
  message: string
  status?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

// Error Types
export interface ApiError {
  detail: string
  status?: number
}
