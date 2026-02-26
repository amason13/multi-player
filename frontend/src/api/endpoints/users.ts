/**
 * Users API Endpoints
 */
import { apiClient } from '../client'
import { ProfileResponse } from '../types/api'

export const usersApi = {
  getProfile: () =>
    apiClient.get<ProfileResponse>('/api/users/profile'),
}
