/**
 * Authentication and User Types
 */

export interface User {
  id: number
  email: string
  username: string
  full_name: string
  role: UserRole
  is_active: boolean
  is_verified: boolean
  created_at: string
}

export type UserRole = 'participant' | 'organizer' | 'judge' | 'admin'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
  full_name: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface TokenRefreshRequest {
  refresh_token: string
}

export interface TokenRefreshResponse {
  access_token: string
  token_type: string
}

export interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  loading: boolean
}
