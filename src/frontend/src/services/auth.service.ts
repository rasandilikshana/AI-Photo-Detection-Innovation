/**
 * Authentication API Service
 */

import api from './api'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  TokenRefreshRequest,
  TokenRefreshResponse,
  User,
} from '@/types/auth.types'

export const authService = {
  /**
   * Register a new user
   */
  async register(data: RegisterRequest): Promise<User> {
    const response = await api.post<User>('/auth/register', data)
    return response.data
  },

  /**
   * Login user
   */
  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/login', data)
    return response.data
  },

  /**
   * Refresh access token
   */
  async refreshToken(data: TokenRefreshRequest): Promise<TokenRefreshResponse> {
    const response = await api.post<TokenRefreshResponse>('/auth/refresh', data)
    return response.data
  },

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/users/me')
    return response.data
  },

  /**
   * Logout (client-side only)
   */
  logout(): void {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  },
}

export default authService
