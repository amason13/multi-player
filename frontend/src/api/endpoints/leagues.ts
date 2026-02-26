/**
 * Leagues API Endpoints
 */
import { apiClient } from '../client'
import {
  CreateLeagueRequest,
  LeagueResponse,
  LeaguesListResponse,
  LeagueDetailsResponse,
} from '../types/api'

export const leaguesApi = {
  create: (data: CreateLeagueRequest) =>
    apiClient.post<LeagueResponse>('/api/leagues', data),

  list: () =>
    apiClient.get<LeaguesListResponse>('/api/leagues'),

  get: (leagueId: string) =>
    apiClient.get<LeagueDetailsResponse>(`/api/leagues/${leagueId}`),
}
