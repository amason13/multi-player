# Lambda Handler Functions - Production-Ready Implementation

## Overview

Created 6 production-ready Lambda handler functions for the Multi-Player fantasy football platform, implementing core access patterns with AWS Lambda Powertools, Pydantic validation, and comprehensive error handling.

## Handlers Created

### 1. **Get User Profile** (Pattern #1)
**File:** `backend/src/functions/users/profile/app.py`

- **Endpoint:** `GET /users/profile`
- **Description:** Retrieves the authenticated user's profile information
- **Features:**
  - Extracts user_id from Cognito claims
  - Validates response with Pydantic model
  - Returns user profile with all metadata
  - Proper error handling (401, 404, 500)
  - CloudWatch logging with correlation IDs
  - Metrics tracking for monitoring

**Response (200):**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "Fantasy football enthusiast",
  "country": "US",
  "timezone": "America/New_York",
  "account_status": "ACTIVE",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-20T14:45:00"
}
```

---

### 2. **List User's Leagues** (Pattern #2)
**File:** `backend/src/functions/leagues/list/app.py`

- **Endpoint:** `GET /users/leagues?limit=10&offset=0`
- **Description:** Lists all leagues the user is a member of
- **Features:**
  - Pagination support (limit, offset)
  - Validates pagination parameters (1-100)
  - Retrieves full league details for each item
  - Pydantic response validation
  - Comprehensive error handling
  - Metrics for pagination tracking

**Response (200):**
```json
{
  "leagues": [
    {
      "league_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Premier League 2024",
      "description": "Fantasy football league",
      "owner_id": "550e8400-e29b-41d4-a716-446655440001",
      "member_count": 12,
      "game_count": 38,
      "status": "ACTIVE",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-20T14:45:00"
    }
  ],
  "count": 1
}
```

---

### 3. **Get League Details** (Pattern #4)
**File:** `backend/src/functions/leagues/get/app.py`

- **Endpoint:** `GET /leagues/{leagueId}`
- **Description:** Retrieves detailed information about a specific league
- **Features:**
  - Membership verification before access
  - Validates league exists
  - Returns comprehensive league metadata
  - Proper authorization checks
  - Detailed error messages
  - Tracer integration for distributed tracing

**Response (200):**
```json
{
  "league": {
    "league_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Premier League 2024",
    "description": "Fantasy football league",
    "owner_id": "550e8400-e29b-41d4-a716-446655440001",
    "member_count": 12,
    "game_count": 38,
    "status": "ACTIVE",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-20T14:45:00"
  }
}
```

---

### 4. **List League Members** (Pattern #5)
**File:** `backend/src/functions/leagues/members/list/app.py`

- **Endpoint:** `GET /leagues/{leagueId}/members?limit=20&offset=0`
- **Description:** Lists all members of a specific league
- **Features:**
  - Membership verification
  - Pagination support (limit, offset)
  - Returns member details (user_id, role, joined_at)
  - Validates league exists
  - Comprehensive error handling
  - Metrics for member list operations

**Response (200):**
```json
{
  "members": [
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440001",
      "role": "owner",
      "joined_at": "2024-01-01T00:00:00"
    },
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440002",
      "role": "member",
      "joined_at": "2024-01-05T10:30:00"
    }
  ],
  "count": 2
}
```

---

### 5. **Submit Prediction** (Pattern #13)
**File:** `backend/src/functions/predictions/submit/app.py`

- **Endpoint:** `POST /predictions/submit`
- **Description:** Submits a prediction for a match in a league
- **Features:**
  - Supports both POINTS_BASED and LAST_MAN_STANDING game types
  - Separate Pydantic models for each game type
  - Validates predicted values (scores, winner)
  - Membership verification
  - Generates unique prediction IDs
  - Comprehensive input validation
  - Detailed error messages for validation failures

**Request Body (Points-Based):**
```json
{
  "league_id": "league-uuid",
  "round_number": 1,
  "match_id": "match-uuid",
  "predicted_home_score": 2,
  "predicted_away_score": 1,
  "confidence_level": 8,
  "reasoning": "Home team is stronger"
}
```

**Request Body (Last Man Standing):**
```json
{
  "league_id": "league-uuid",
  "round_number": 1,
  "match_id": "match-uuid",
  "predicted_winner": "HOME",
  "confidence_level": 7,
  "reasoning": "Home team has better form"
}
```

**Response (201):**
```json
{
  "prediction_id": "pred-uuid",
  "user_id": "user-uuid",
  "league_id": "league-uuid",
  "round_number": 1,
  "match_id": "match-uuid",
  "game_type": "POINTS_BASED",
  "status": "PENDING",
  "created_at": "2024-01-20T14:45:00"
}
```

---

### 6. **Get Standings** (Patterns #16-17)
**File:** `backend/src/functions/standings/get/app.py`

- **Endpoint:** `GET /leagues/{leagueId}/standings?gameType=POINTS_BASED&roundNumber=1&isFinal=false`
- **Description:** Retrieves standings for a league or game round
- **Features:**
  - Supports both POINTS_BASED and LAST_MAN_STANDING standings
  - Flexible round selection (specific round or final)
  - Membership verification
  - Returns ranked player standings with stats
  - Handles both active and eliminated players (LMS)
  - Comprehensive error handling
  - Metrics for standings retrieval

**Response (200):**
```json
{
  "league_id": "league-uuid",
  "game_type": "POINTS_BASED",
  "round_number": 1,
  "is_final": false,
  "total_participants": 12,
  "active_participants": 12,
  "standings": [
    {
      "rank": 1,
      "user_id": "user-uuid-1",
      "user_name": "John Doe",
      "avatar_url": "https://example.com/avatar.jpg",
      "total_points": 145,
      "games_played": 5,
      "average_points_per_game": 29.0,
      "prediction_accuracy": 85.5
    },
    {
      "rank": 2,
      "user_id": "user-uuid-2",
      "user_name": "Jane Smith",
      "avatar_url": "https://example.com/avatar2.jpg",
      "total_points": 138,
      "games_played": 5,
      "average_points_per_game": 27.6,
      "prediction_accuracy": 82.0
    }
  ]
}
```

---

## Key Features Implemented

### AWS Lambda Powertools Integration
- ✅ **@logger.inject_lambda_context** - Automatic correlation ID injection
- ✅ **@tracer.capture_lambda_handler** - Distributed tracing with X-Ray
- ✅ **@metrics.log_metrics** - CloudWatch metrics with cold start tracking

### Input Validation
- ✅ **Pydantic Models** - Type-safe request/response validation
- ✅ **Field Validators** - Custom validation logic (e.g., predicted_winner)
- ✅ **Range Validation** - Confidence levels (1-10), pagination limits (1-100)
- ✅ **Enum Validation** - Game types, roles, statuses

### Error Handling
- ✅ **Custom Exceptions** - UnauthorizedError, NotFoundError, ValidationError
- ✅ **HTTP Status Codes** - 200, 201, 400, 401, 404, 500
- ✅ **Error Codes** - Application-specific error codes for client handling
- ✅ **Detailed Messages** - Clear error messages for debugging

### Security
- ✅ **Cognito Integration** - User ID extraction from JWT claims
- ✅ **Membership Verification** - Access control for league resources
- ✅ **Authorization Checks** - Verify user belongs to league before access

### Observability
- ✅ **CloudWatch Logging** - Structured logs with correlation IDs
- ✅ **Metrics** - Request counts, success/error metrics
- ✅ **Distributed Tracing** - X-Ray integration for request tracing
- ✅ **Detailed Docstrings** - Comprehensive documentation

### Code Quality
- ✅ **Type Hints** - Full type annotations throughout
- ✅ **Comprehensive Docstrings** - Detailed function documentation
- ✅ **Error Context** - Informative error messages
- ✅ **Pagination** - Proper offset/limit handling
- ✅ **Response Validation** - Pydantic validation of all responses

---

## Repository Integration

All handlers use the following repositories:
- **UserRepository** - User profile operations
- **LeagueRepository** - League and member operations
- **PredictionRepository** - Prediction submission and retrieval
- **StandingsRepository** - Standings computation and retrieval

---

## File Structure

```
backend/src/functions/
├── users/
│   └── profile/
│       ├── app.py (UPDATED)
│       └── requirements.txt
├── leagues/
│   ├── list/
│   │   ├── app.py (NEW)
│   │   └── requirements.txt
│   ├── get/
│   │   ├── app.py (UPDATED)
│   │   └── requirements.txt
│   └── members/
│       └── list/
│           ├── app.py (NEW)
│           └── requirements.txt
├── predictions/
│   └── submit/
│       ├── app.py (NEW)
│       └── requirements.txt
└── standings/
    └── get/
        ├── app.py (NEW)
        └── requirements.txt
```

---

## Testing Recommendations

### Unit Tests
- Test Pydantic model validation
- Test error handling for each exception type
- Test pagination parameter validation
- Test membership verification logic

### Integration Tests
- Test with actual DynamoDB (local or test environment)
- Test Cognito claim extraction
- Test repository method calls
- Test response validation

### Load Tests
- Test with concurrent requests
- Monitor Lambda cold start times
- Monitor CloudWatch metrics
- Test pagination with large datasets

---

## Deployment Notes

1. **Environment Variables Required:**
   - `TABLE_NAME` - DynamoDB table name
   - `USER_POOL_ID` - Cognito user pool ID (for auth handlers)

2. **IAM Permissions Required:**
   - `dynamodb:GetItem`
   - `dynamodb:Query`
   - `dynamodb:PutItem`
   - `dynamodb:UpdateItem`
   - `logs:CreateLogGroup`
   - `logs:CreateLogStream`
   - `logs:PutLogEvents`
   - `xray:PutTraceSegments`
   - `xray:PutTelemetryRecords`

3. **Lambda Configuration:**
   - Memory: 512 MB (minimum)
   - Timeout: 30 seconds
   - Ephemeral Storage: 512 MB
   - Layers: Common layer with dependencies

---

## Production Checklist

- [x] All handlers use Powertools decorators
- [x] Cognito claims extraction implemented
- [x] Pydantic validation for all inputs/outputs
- [x] Repository method calls implemented
- [x] Standardized response format
- [x] Comprehensive error handling
- [x] HTTP status codes properly set
- [x] CloudWatch logging with correlation IDs
- [x] Type hints throughout
- [x] Detailed docstrings
- [x] Metrics tracking
- [x] Distributed tracing support

