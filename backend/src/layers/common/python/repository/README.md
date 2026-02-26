# Repository Layer - Multi-Player Fantasy Football Platform

Comprehensive repository classes for DynamoDB operations in the Multi-Player fantasy football/tipping competition platform.

## Overview

The repository layer provides a clean abstraction over DynamoDB operations, implementing all access patterns from the single-table design data model. Each repository class handles a specific domain entity and provides methods for CRUD operations, queries, and business logic.

## Repository Classes

### 1. UserRepository
Handles user profile, preferences, settings, and statistics operations.

**Key Methods:**
- `get_profile(user_id)` - Get user profile
- `update_profile(user_id, updates)` - Update profile
- `get_preferences(user_id)` - Get user preferences
- `get_statistics(user_id, league_id)` - Get user stats for league
- `get_user_data(user_id)` - Get all user data
- `create_user_complete(profile, preferences, settings)` - Create complete user

**Access Patterns:**
- Pattern #1: Get user profile
- Pattern #2: Get user's leagues (via get_user_data)

### 2. LeagueRepository
Handles league creation, member management, and game associations.

**Key Methods:**
- `create_league(league_id, name, owner_id, ...)` - Create league
- `get_league(league_id)` - Get league details
- `add_member(league_id, user_id, role)` - Add member
- `get_members(league_id)` - Get all members
- `add_game(league_id, game_id)` - Add game to league
- `get_games(league_id)` - Get all games
- `get_standings(league_id, game_type, round_number)` - Get standings

**Access Patterns:**
- Pattern #3: Create league
- Pattern #4: Get league details
- Pattern #5: Get league members
- Pattern #6: Add member to league
- Pattern #7: Get league's games

### 3. GameRepository
Handles game creation, member management, round associations, and LMS-specific operations.

**Key Methods:**
- `create_game(game_id, league_id, game_type, ...)` - Create game
- `get_game(game_id)` - Get game details
- `add_member(game_id, user_id)` - Add member
- `get_members(game_id)` - Get all members
- `add_round(game_id, round_id, round_number)` - Add round
- `get_rounds(game_id)` - Get all rounds
- `eliminate_member(game_id, user_id, round_number)` - Eliminate member (LMS)
- `is_eliminated(game_id, user_id)` - Check elimination status

**Access Patterns:**
- Pattern #8: Create game
- Pattern #9: Get game details
- Pattern #10: Get game's rounds
- Pattern #16: Get game standings
- Pattern #20: Check if user eliminated (LMS)

### 4. RoundRepository
Handles round creation, match management, and status tracking.

**Key Methods:**
- `create_round(round_id, league_id, game_id, round_number, ...)` - Create round
- `get_round(league_id, round_number)` - Get round details
- `add_match(league_id, round_number, match_id, ...)` - Add match
- `get_matches(league_id, round_number)` - Get all matches
- `set_match_result(league_id, round_number, match_id, home_score, away_score)` - Set result
- `update_round_status(league_id, round_number, status)` - Update status
- `get_active_rounds(league_id)` - Get active rounds

**Access Patterns:**
- Pattern #11: Create round
- Pattern #12: Get round details
- Pattern #10: Get game's rounds
- Pattern #15: Get all predictions for round

### 5. PredictionRepository
Handles prediction submission, scoring, and user prediction history.

**Key Methods:**
- `submit_points_based_prediction(...)` - Submit points-based prediction
- `submit_lms_prediction(...)` - Submit LMS prediction
- `get_prediction(user_id, league_id, round_number, match_id)` - Get prediction
- `get_user_predictions_for_round(user_id, league_id, round_number)` - Get round predictions
- `score_points_based_prediction(...)` - Score points-based prediction
- `score_lms_prediction(...)` - Score LMS prediction
- `lock_prediction(...)` - Lock prediction
- `get_pick_history(user_id, game_id)` - Get pick history (LMS)

**Access Patterns:**
- Pattern #13: Submit prediction
- Pattern #14: Get user's predictions for round
- Pattern #15: Get all predictions for round
- Pattern #19: Get user's pick history (LMS)

### 6. StandingsRepository
Handles standings computation, retrieval, and ranking management.

**Key Methods:**
- `create_standings(standings_id, league_id, game_id, ...)` - Create standings
- `get_standings(league_id, game_type, round_number)` - Get standings
- `get_final_standings(league_id, game_type)` - Get final standings
- `get_user_standing(league_id, game_type, round_number, user_id)` - Get user standing
- `get_top_players(league_id, game_type, round_number, limit)` - Get top players
- `compute_points_based_standings(...)` - Compute points-based standings
- `compute_lms_standings(...)` - Compute LMS standings
- `lock_standings(league_id, game_type, round_number, locked_by)` - Lock standings

**Access Patterns:**
- Pattern #16: Get game standings
- Pattern #17: Get league standings
- Pattern #18: Get user's stats in league

### 7. InvitationRepository
Handles league invitation creation, retrieval, and response.

**Key Methods:**
- `create_invitation(invitation_id, league_id, inviter_id, invitee_email, ...)` - Create invitation
- `get_invitation(invitation_id)` - Get invitation
- `get_pending_invitations(user_id)` - Get pending invitations
- `accept_invitation(invitation_id, invitee_id)` - Accept invitation
- `reject_invitation(invitation_id, invitee_id)` - Reject invitation
- `send_bulk_invitations(league_id, inviter_id, emails)` - Send bulk invitations
- `resend_invitation(invitation_id)` - Resend invitation

**Access Patterns:**
- Pattern #21: Send league invitation
- Pattern #22: Get pending invitations
- Pattern #23: Accept/reject invitation

## Usage Examples

### Basic Usage

```python
from repository import LeagueRepository, GameRepository, PredictionRepository

# Initialize repositories
league_repo = LeagueRepository()
game_repo = GameRepository()
pred_repo = PredictionRepository()

# Create a league
league = league_repo.create_league(
    league_id='league-001',
    name='Premier League 2024-25',
    owner_id='user-001'
)

# Add members
league_repo.add_member('league-001', 'user-002', 'MEMBER')
league_repo.add_member('league-001', 'user-003', 'MEMBER')

# Create a game
game = game_repo.create_game(
    game_id='game-001',
    league_id='league-001',
    game_type='POINTS_BASED'
)

# Add game members
game_repo.add_member('game-001', 'user-002')
game_repo.add_member('game-001', 'user-003')

# Submit predictions
pred_repo.submit_points_based_prediction(
    prediction_id='pred-001',
    user_id='user-002',
    league_id='league-001',
    round_number=1,
    match_id='match-001',
    predicted_home_score=2,
    predicted_away_score=1,
    confidence_level=8
)
```

### Complete Workflow

See `examples.py` for a complete workflow example that demonstrates:
1. League creation
2. Member management
3. Game creation
4. Round and match creation
5. Prediction submission
6. Match result setting
7. Prediction scoring
8. Standings computation

## Error Handling

All repositories use custom exceptions from `utils.exceptions`:

- `ValidationError` - Invalid input data
- `NotFoundError` - Resource not found
- `ConflictError` - Resource already exists
- `UnauthorizedError` - User not authorized

Example:

```python
from utils.exceptions import NotFoundError, ValidationError

try:
    league = league_repo.get_league('invalid-id')
    if not league:
        raise NotFoundError("League not found")
except ValidationError as e:
    print(f"Validation error: {e.message}")
except NotFoundError as e:
    print(f"Not found: {e.message}")
```

## Logging

All repositories use AWS Lambda Powertools Logger for structured logging:

```python
from aws_lambda_powertools import Logger

logger = Logger()

# Logs are automatically structured with context
logger.info(f"Created league: {league_id}")
logger.warning("get_match_predictions requires GSI - not implemented")
logger.exception(f"Error getting item: {e}")
```

## DynamoDB Access Patterns

All repositories implement the 24 access patterns from the data model:

| Pattern | Repository | Method |
|---------|-----------|--------|
| 1 | UserRepository | get_profile() |
| 2 | UserRepository | get_user_data() |
| 3 | LeagueRepository | create_league() |
| 4 | LeagueRepository | get_league() |
| 5 | LeagueRepository | get_members() |
| 6 | LeagueRepository | add_member() |
| 7 | LeagueRepository | get_games() |
| 8 | GameRepository | create_game() |
| 9 | GameRepository | get_game() |
| 10 | GameRepository | get_rounds() |
| 11 | RoundRepository | create_round() |
| 12 | RoundRepository | get_round() |
| 13 | PredictionRepository | submit_*_prediction() |
| 14 | PredictionRepository | get_user_predictions_for_round() |
| 15 | PredictionRepository | get_match_predictions() |
| 16 | StandingsRepository | get_standings() |
| 17 | StandingsRepository | get_standings() |
| 18 | StandingsRepository | get_user_standing() |
| 19 | PredictionRepository | get_pick_history() |
| 20 | GameRepository | is_eliminated() |
| 21 | InvitationRepository | create_invitation() |
| 22 | InvitationRepository | get_pending_invitations() |
| 23 | InvitationRepository | accept_invitation() |
| 24 | StandingsRepository | compute_*_standings() |

## Performance Considerations

### Query Optimization
- All queries use GetItem or Query operations (no Scans)
- Partition keys are high-cardinality to avoid hot partitions
- Sort keys support efficient range queries with `begins_with`
- Projection expressions reduce data transfer

### Caching Strategy
- Cache frequently accessed items (profiles, standings)
- Use TTL for temporary data
- Invalidate cache on updates

### Batch Operations
- Use batch_writer() for bulk inserts
- Batch operations reduce API calls
- Max 25 items per batch

## Testing

Run the examples to test all repositories:

```bash
python repository/examples.py
```

## Future Enhancements

- [ ] Implement GSI queries for cross-entity lookups
- [ ] Add pagination support with ExclusiveStartKey
- [ ] Add transaction support for atomic operations
- [ ] Add caching layer with TTL
- [ ] Add metrics and monitoring
- [ ] Add retry logic with exponential backoff
- [ ] Add data validation with Pydantic models

## References

- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Single-Table Design](https://www.alexdebrie.com/posts/dynamodb-single-table/)
- [AWS Lambda Powertools](https://docs.aws.amazon.com/lambda/latest/dg/python-logging.html)
- [Boto3 DynamoDB](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html)
