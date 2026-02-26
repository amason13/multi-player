/**
 * API Type Definitions
 * These types mirror the backend API contracts
 */

// Auth Types
export interface SignUpRequest {
  email: string
  password: string
  name: string
}

export interface SignInRequest {
  email: string
  password: string
}

export interface AuthResponse {
  message: string
  accessToken: string
  idToken: string
  refreshToken: string
  expiresIn: number
}

// League Types
export interface League {
  id: string
  name: string
  description: string
  sport: string
  owner_id: string
  member_count: number
  created_at: string
}

export interface CreateLeagueRequest {
  name: string
  description?: string
  sport?: string
}

export interface LeagueResponse {
  message: string
  league: League
}

export interface LeaguesListResponse {
  leagues: League[]
  count: number
}

export interface LeagueDetailsResponse {
  league: League & {
    members: LeagueMember[]
  }
}

export interface LeagueMember {
  user_id: string
  role: 'owner' | 'member'
  joined_at: string
}

// User Types
export interface UserProfile {
  user_id: string
  email: string
  name: string
  created_at?: string
}

export interface ProfileResponse {
  profile: UserProfile
}

// Error Response
export interface ErrorResponse {
  error: string
  statusCode: number
  errorCode?: string
}
