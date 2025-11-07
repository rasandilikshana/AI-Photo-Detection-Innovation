/**
 * Axios API Client Configuration
 * Handles authentication, token refresh, and error handling
 */

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/store/auth'

// API Base URLs
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'
const AI_DETECTION_URL = import.meta.env.VITE_AI_DETECTION_URL || 'http://localhost:8001'

// Create main API instance for Competition Service
const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Create AI Detection API instance
export const aiApi: AxiosInstance = axios.create({
  baseURL: `${AI_DETECTION_URL}/api/v1`,
  timeout: 60000, // Longer timeout for image processing
  headers: {
    'Content-Type': 'multipart/form-data',
  },
})

// Request interceptor - Add JWT token to requests
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const authStore = useAuthStore()
    const token = authStore.token || localStorage.getItem('access_token')

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - Handle errors and token refresh
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // Handle 401 Unauthorized - Try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const authStore = useAuthStore()
        const refreshToken = authStore.refreshToken || localStorage.getItem('refresh_token')

        if (!refreshToken) {
          // No refresh token, logout user
          authStore.logout()
          return Promise.reject(error)
        }

        // Try to refresh the access token
        const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        })

        const { access_token } = response.data

        // Update token in store and localStorage
        authStore.token = access_token
        localStorage.setItem('access_token', access_token)

        // Retry original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`
        }

        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed, logout user
        const authStore = useAuthStore()
        authStore.logout()
        return Promise.reject(refreshError)
      }
    }

    // Handle other errors
    return Promise.reject(error)
  }
)

// Error handling helper
export interface ApiError {
  message: string
  status?: number
  details?: any
}

export const handleApiError = (error: any): ApiError => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<any>

    if (axiosError.response) {
      // Server responded with error
      return {
        message: axiosError.response.data?.detail || axiosError.response.data?.message || 'An error occurred',
        status: axiosError.response.status,
        details: axiosError.response.data,
      }
    } else if (axiosError.request) {
      // Request made but no response
      return {
        message: 'No response from server. Please check your connection.',
        status: 0,
      }
    }
  }

  // Generic error
  return {
    message: error?.message || 'An unexpected error occurred',
  }
}

export default api
