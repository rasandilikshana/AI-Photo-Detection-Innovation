/**
 * Competition Types
 */

export interface Competition {
  id: number
  title: string
  slug: string
  description?: string
  rules?: string
  cover_image_url?: string
  submission_start: string
  submission_end: string
  judging_start?: string
  judging_end?: string
  results_announcement?: string
  status: CompetitionStatus
  max_submissions_per_user: number
  require_raw_files: boolean
  allowed_file_types?: string[]
  max_file_size_mb: number
  entry_fee?: number
  prize_amount?: number
  prize_description?: string
  total_submissions: number
  total_participants: number
  organizer_id: number
  created_at: string
  updated_at: string
}

export type CompetitionStatus = 'draft' | 'open' | 'closed' | 'judging' | 'completed'

export interface CompetitionCreateRequest {
  title: string
  description?: string
  rules?: string
  submission_start: string
  submission_end: string
  judging_start?: string
  judging_end?: string
  results_announcement?: string
  max_submissions_per_user?: number
  require_raw_files?: boolean
  allowed_file_types?: string[]
  max_file_size_mb?: number
  entry_fee?: number
  prize_amount?: number
  prize_description?: string
}

export interface CompetitionUpdateRequest {
  title?: string
  description?: string
  rules?: string
  submission_start?: string
  submission_end?: string
  judging_start?: string
  judging_end?: string
  results_announcement?: string
  status?: CompetitionStatus
  max_submissions_per_user?: number
  require_raw_files?: boolean
  allowed_file_types?: string[]
  max_file_size_mb?: number
  entry_fee?: number
  prize_amount?: number
  prize_description?: string
}

export interface CompetitionFilters {
  status?: CompetitionStatus
  search?: string
  skip?: number
  limit?: number
}

export interface CompetitionState {
  competitions: Competition[]
  currentCompetition: Competition | null
  filters: CompetitionFilters
  loading: boolean
  total: number
}

export interface Pagination {
  skip: number
  limit: number
  total: number
  hasMore: boolean
}
