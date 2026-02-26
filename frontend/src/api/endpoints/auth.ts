/**
 * Authentication API Endpoints
 */
import { apiClient } from '../client'
import { SignUpRequest, SignInRequest, AuthResponse } from '../types/api'

export const authApi = {
  signup: (data: SignUpRequest) =>
    apiClient.post<AuthResponse>('/api/auth/signup', data),

  signin: (data: SignInRequest) =>
    apiClient.post<AuthResponse>('/api/auth/signin', data),
}
