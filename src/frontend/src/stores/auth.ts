import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, apiClient } from '@/api'
import type { User, UserLogin, UserRegister } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = computed(() => !!user.value)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function login(credentials: UserLogin) {
    isLoading.value = true
    error.value = null
    try {
      const response = await authApi.login(credentials)
      user.value = response.user
      apiClient.setToken(response.access_token)
      apiClient.setRefreshToken(response.refresh_token)
      return response
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Login failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function register(data: UserRegister) {
    isLoading.value = true
    error.value = null
    try {
      const newUser = await authApi.register(data)
      // Auto-login after registration
      await login({ email: data.email, password: data.password })
      return newUser
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Registration failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      user.value = null
      apiClient.clearTokens()
    }
  }

  async function fetchCurrentUser() {
    if (!localStorage.getItem('access_token')) {
      return
    }

    isLoading.value = true
    try {
      user.value = await authApi.getCurrentUser()
    } catch (err) {
      console.error('Failed to fetch current user:', err)
      apiClient.clearTokens()
      user.value = null
    } finally {
      isLoading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
    fetchCurrentUser,
    clearError,
  }
})
