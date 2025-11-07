/**
 * Authentication Store
 * Manages user authentication state and operations
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '@/services/auth.service'
import type { User, LoginRequest, RegisterRequest, AuthState } from '@/types/auth.types'
import { handleApiError } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isOrganizer = computed(() => user.value?.role === 'organizer' || user.value?.role === 'admin')
  const isJudge = computed(() => user.value?.role === 'judge' || user.value?.role === 'admin')
  const userRole = computed(() => user.value?.role || null)

  // Actions

  /**
   * Initialize auth state from localStorage
   */
  function initializeAuth() {
    const storedToken = localStorage.getItem('access_token')
    const storedRefreshToken = localStorage.getItem('refresh_token')
    const storedUser = localStorage.getItem('user')

    if (storedToken && storedUser) {
      token.value = storedToken
      refreshToken.value = storedRefreshToken
      user.value = JSON.parse(storedUser)
    }
  }

  /**
   * Register new user
   */
  async function register(data: RegisterRequest): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      const newUser = await authService.register(data)

      // After registration, user needs to login
      // So we don't set the auth state here
      return true
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Login user
   */
  async function login(credentials: LoginRequest): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      const response = await authService.login(credentials)

      // Set auth state
      token.value = response.access_token
      refreshToken.value = response.refresh_token
      user.value = response.user

      // Persist to localStorage
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      localStorage.setItem('user', JSON.stringify(response.user))

      return true
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Logout user
   */
  function logout() {
    // Clear state
    user.value = null
    token.value = null
    refreshToken.value = null
    error.value = null

    // Clear localStorage
    authService.logout()
  }

  /**
   * Fetch current user profile
   */
  async function fetchCurrentUser(): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const currentUser = await authService.getCurrentUser()
      user.value = currentUser
      localStorage.setItem('user', JSON.stringify(currentUser))
    } catch (err) {
      const apiError = handleApiError(err)
      error.value = apiError.message
      // If fetching user fails, logout
      logout()
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Update user in state (after profile update)
   */
  function updateUser(updatedUser: User) {
    user.value = updatedUser
    localStorage.setItem('user', JSON.stringify(updatedUser))
  }

  /**
   * Clear error
   */
  function clearError() {
    error.value = null
  }

  return {
    // State
    user,
    token,
    refreshToken,
    loading,
    error,
    // Getters
    isAuthenticated,
    isAdmin,
    isOrganizer,
    isJudge,
    userRole,
    // Actions
    initializeAuth,
    register,
    login,
    logout,
    fetchCurrentUser,
    updateUser,
    clearError,
  }
})
