import client from './client'
import type { User, UserRegister, UserLogin, TokenResponse } from '@/types'

export const authApi = {
  async register(data: UserRegister): Promise<User> {
    const response = await client.post('/auth/register', data)
    return response.data
  },

  async login(data: UserLogin): Promise<TokenResponse> {
    const response = await client.post('/auth/login', data)
    return response.data
  },

  async getCurrentUser(): Promise<User> {
    const response = await client.get('/auth/me')
    return response.data
  },

  async logout(): Promise<void> {
    await client.post('/auth/logout')
  },
}
