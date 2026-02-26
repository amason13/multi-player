# STANDINGS Entity Specification - Multi-Player Fantasy Football Platform

## Overview
The STANDINGS entity represents leaderboards and rankings at both game and league levels. Standings are computed/derived from predictions and match results, updated in real-time as predictions are scored. This specification supports both Points-Based and Last Man Standing (LMS) competition types with hierarchical ranking (game-level and league-level).

## DynamoDB Key Schema

### Primary Keys
```
PK (Partition Key): LEAGUE#{league_id}
SK (Sort Key): STANDINGS#{game_type}#{round_number} | STANDINGS#{game_type}#FINAL
```

### Global Secondary Index (GSI1)
```
GSI1PK: GAME#{game_id}
GSI1SK: STANDINGS#{game_type}#{round_number}
```

### Global Secondary Index (GSI2)
```
GSI2PK: STANDINGS_RANK#{game_type}#{rank}
GSI2SK: league#{league_id}#{round_number}
```

### Global Secondary Index (GSI3)
```
GSI3PK: USER#{user_id}
GSI3SK: STANDINGS#{league_id}#{game_type}
```

### Access Patterns
1. **Get league standings**: `PK=LEAGUE#{league_id}, SK=STANDINGS#{game_type}#{round_number}`
2. **Get final standings**: `PK=LEAGUE#{league_id}, SK=STANDINGS#{game_type}#FINAL`
3. **Get game standings**: `GSI1PK=GAME#{game_id}, GSI1SK=STANDINGS#{game_type}#{round_number}`
4. **Get user's ranking**: `GSI3PK=USER#{user_id}, GSI3SK=STANDINGS#{league_id}#{game_type}`
5. **Get top 10 players**: `GSI2PK=STANDINGS_RANK#{game_type}#{rank}, GSI2SK begins_with league#{league_id}#`
6. **Get standings by rank**: `GSI2PK=STANDINGS_RANK#{game_type}#{rank}, GSI2SK=league#{league_id}#{round_number}`

---

## Entity Attributes

### STANDINGS Item (SK=STANDINGS#{game_type}#{round_number})

#### Required Attributes

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `PK` | String | Partition key | `LEAGUE#league-001` | Format: `LEAGUE#{league_id}` |
| `SK` | String | Sort key | `STANDINGS#POINTS_BASED#1` | Format: `STANDINGS#{game_type}#{round_number}` |
| `GSI1PK` | String | GSI1 partition key | `GAME#game-001` | Format: `GAME#{game_id}` |
| `GSI1SK` | String | GSI1 sort key | `STANDINGS#POINTS_BASED#1` | Format: `STANDINGS#{game_type}#{round_number}` |
| `GSI2PK` | String | GSI2 partition key | `STANDINGS_RANK#POINTS_BASED#1` | Format: `STANDINGS_RANK#{game_type}#{rank}` |
| `GSI2SK` | String | GSI2 sort key | `league#league-001#1` | Format: `league#{league_id}#{round_number}` |
| `entity_type` | String | Entity classification | `STANDINGS` | Fixed value |
| `standings_id` | String | Unique standings identifier (UUID v4) | `550e8400-e29b-41d4-a716-446655440000` | Immutable, globally unique |
| `league_id` | String | Parent league identifier | `league-001` | Reference to LEAGUE |
| `game_id` | String | Parent game identifier | `game-001` | Reference to GAME |
| `game_type` | String | Competition type | `POINTS_BASED` | POINTS_BASED, LAST_MAN_STANDING |
| `round_number` | Number | Round number | `1` | Positive integer or 0 for final |
| `is_final` | Boolean | Is final standings | `false` | Default: false |
| `total_participants` | Number | Total league members | `50` | Positive integer |
| `active_participants` | Number | Active participants (LMS) | `45` | Non-negative integer |
| `eliminated_participants` | Number | Eliminated participants (LMS) | `5` | Non-negative integer |
| `standings_data` | List | Array of player standings | See below | Array of objects |
| `created_at` | String | Creation timestamp | `2024-02-10T16:00:00.000Z` | ISO 8601 format |
| `updated_at` | String | Last update timestamp | `2024-02-10T16:30:00.000Z` | ISO 8601 format |
| `computed_at` | String | When standings were computed | `2024-02-10T16:30:00.000Z` | ISO 8601 format |

#### Optional Attributes

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `title` | String | Standings display title | `Week 1 Standings` | Max 200 characters |
| `description` | String | Standings description | `Current standings after round 1` | Max 1000 characters |
| `is_locked` | Boolean | Standings locked from updates | `false` | Default: false |
| `locked_at` | String | When standings were locked | `2024-02-17T23:59:59Z` | ISO 8601 format |
| `locked_by` | String | User who locked standings | `admin-user-id` | User ID |
| `notes` | String | Admin notes | `Verified and approved` | Max 500 characters |
| `metadata` | Map | Custom metadata | `{"version": "1.0"}` | JSON object |

---

### STANDINGS_DATA Item (Nested in standings_data array)

Each entry in the `standings_data` array represents a player's standing.

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `rank` | Number | Current rank | `1` | Positive integer |
| `previous_rank` | Number | Previous round rank | `2` | Positive integer or 0 |
| `rank_change` | Number | Rank change (positive = improvement) | `1` | Integer (can be negative) |
| `user_id` | String | User identifier | `user-001` | Reference to USER |
| `user_name` | String | User display name | `John Doe` | Max 100 characters |
| `avatar_url` | String | User avatar URL | `https://cdn.example.com/avatar.jpg` | HTTPS URL |

#### Points-Based Specific Fields

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `total_points` | Number | Total points earned | `250` | Non-negative integer |
| `round_points` | Number | Points earned this round | `25` | Non-negative integer |
| `games_played` | Number | Games/rounds played | `1` | Non-negative integer |
| `average_points_per_game` | Number | Average points per game | `250.0` | Non-negative decimal |
| `highest_score` | Number | Highest single-game score | `50` | Non-negative integer |
| `lowest_score` | Number | Lowest single-game score | `10` | Non-negative integer |
| `correct_predictions` | Number | Correct predictions | `8` | Non-negative integer |
| `total_predictions` | Number | Total predictions | `10` | Non-negative integer |
| `prediction_accuracy` | Number | Prediction accuracy % | `80.0` | 0-100, 2 decimal places |

#### Last Man Standing Specific Fields

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `is_alive` | Boolean | Still alive in competition | `true` | True/false |
| `games_won` | Number | Games won | `5` | Non-negative integer |
| `games_lost` | Number | Games lost | `0` | Non-negative integer |
| `win_percentage` | Number | Win percentage | `100.0` | 0-100, 2 decimal places |
| `consecutive_wins` | Number | Current win streak | `5` | Non-negative integer |
| `consecutive_losses` | Number | Current loss streak | `0` | Non-negative integer |
| `best_consecutive_wins` | Number | Best win streak | `5` | Non-negative integer |
| `lives_remaining` | Number | Lives remaining (if applicable) | `3` | Non-negative integer |
| `eliminated_round` | Number | Round eliminated (if applicable) | `null` | Positive integer or null |

#### Common Fields

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `last_activity_at` | String | Last activity timestamp | `2024-02-10T16:00:00Z` | ISO 8601 format |
| `joined_at` | String | League join date | `2024-01-01T10:30:45.123Z` | ISO 8601 format |
| `is_new_to_league` | Boolean | New member this season | `false` | Default: false |
| `is_returning_champion` | Boolean | Won previous season | `true` | Default: false |

---

## Computed/Derived Fields

These fields are calculated from predictions and match results.

| Field | Calculation | Update Frequency | Example |
|-------|-----------|------------------|---------|
| `rank_change` | `previous_rank - current_rank` | After each round | `1` |
| `average_points_per_game` | `total_points / games_played` | After each round | `250.0` |
| `prediction_accuracy` | `(correct_predictions / total_predictions) * 100` | After each prediction | `80.0` |
| `win_percentage` | `(games_won / (games_won + games_lost)) * 100` | After each game | `100.0` |
| `active_participants` | `Count of users with is_alive=true` | After each round | `45` |
| `eliminated_participants` | `Count of users with is_alive=false` | After each round | `5` |
| `standings_complete` | `active_participants == 0 OR round_number == final` | Real-time | `false` |

---

## Status & Lifecycle

### Standings Lifecycle
```
COMPUTING → PUBLISHED → LOCKED
    ↓           ↓          ↓
    └───────────┴──────────┴─→ ARCHIVED (after season)
```

### Standings States
- **COMPUTING**: Standings being calculated from predictions
- **PUBLISHED**: Standings available for viewing
- **LOCKED**: Standings finalized, no further updates
- **ARCHIVED**: Historical standings (read-only)

---

## Validation Rules

### Rank
- Positive integer
- Unique per standings
- Sequential (no gaps)
- Matches array position

### Points (Points-Based)
- Non-negative integers
- Total points >= round points
- Average points = total points / games played
- Highest score >= lowest score

### Win Percentage (LMS)
- 0-100 with 2 decimal places
- Calculated from games_won and games_lost
- 0% if no games played
- 100% if all games won

### Dates & Times
- ISO 8601 format with millisecond precision
- UTC timezone
- `created_at` <= `updated_at`
- `computed_at` >= `created_at`

### Participant Counts
- `total_participants` >= `active_participants`
- `active_participants` + `eliminated_participants` = `total_participants`
- All non-negative integers

---

## Constraints & Limits

### Size Constraints
- **Item size**: Max 400 KB per item (DynamoDB limit)
- **standings_data array**: Max 10,000 items per standings
- **Title**: Max 200 characters
- **Description**: Max 1000 characters
- **Notes**: Max 500 characters

### Rate Limits
- **Standings creation**: Max 100 per league per season
- **Standings updates**: Max 10000 per minute per league
- **Standings queries**: No limit (read-heavy)
- **Batch operations**: Max 25 items per batch

### Data Retention
- **Active standings**: Indefinite
- **Final standings**: Indefinite (historical tracking)
- **Archived standings**: Indefinite (read-only)
- **Computation logs**: 1 year

### Concurrent Operations
- Multiple users can view standings
- Only system can update standings
- Optimistic locking recommended
- Eventual consistency acceptable

---

## Indexes & Query Patterns

### Primary Key Queries
```
# Get league standings for round
Query: PK=LEAGUE#{league_id}, SK=STANDINGS#{game_type}#{round_number}
Result: Single item with standings_data array
Latency: <10ms

# Get final standings
Query: PK=LEAGUE#{league_id}, SK=STANDINGS#{game_type}#FINAL
Result: Single item with final standings
Latency: <10ms
```

### GSI1 Queries
```
# Get game standings
Query: GSI1PK=GAME#{game_id}, GSI1SK=STANDINGS#{game_type}#{round_number}
Result: Multiple items (one per league)
Latency: <50ms
```

### GSI3 Queries
```
# Get user's standings in league
Query: GSI3PK=USER#{user_id}, GSI3SK=STANDINGS#{league_id}#{game_type}
Result: Single item
Latency: <10ms
```

### Scan Operations (Avoid in Production)
```
# Get all standings (requires scan)
Scan: Filter entity_type = "STANDINGS"
Result: All standings items
Latency: O(n) - expensive, avoid
```

---

## Example Items

### Points-Based Standings (Round 1)
```json
{
  "PK": "LEAGUE#league-001",
  "SK": "STANDINGS#POINTS_BASED#1",
  "GSI1PK": "GAME#game-001",
  "GSI1SK": "STANDINGS#POINTS_BASED#1",
  "GSI2PK": "STANDINGS_RANK#POINTS_BASED#1",
  "GSI2SK": "league#league-001#1",
  "entity_type": "STANDINGS",
  "standings_id": "550e8400-e29b-41d4-a716-446655440000",
  "league_id": "league-001",
  "game_id": "game-001",
  "game_type": "POINTS_BASED",
  "round_number": 1,
  "is_final": false,
  "total_participants": 50,
  "active_participants": 50,
  "eliminated_participants": 0,
  "title": "Week 1 Standings",
  "description": "Current standings after round 1",
  "standings_data": [
    {
      "rank": 1,
      "previous_rank": 0,
      "rank_change": 0,
      "user_id": "user-001",
      "user_name": "John Doe",
      "avatar_url": "https://cdn.example.com/avatar1.jpg",
      "total_points": 50,
      "round_points": 50,
      "games_played": 1,
      "average_points_per_game": 50.0,
      "highest_score": 50,
      "lowest_score": 50,
      "correct_predictions": 10,
      "total_predictions": 10,
      "prediction_accuracy": 100.0,
      "last_activity_at": "2024-02-10T16:00:00Z",
      "joined_at": "2024-01-01T10:30:45.123Z",
      "is_new_to_league": false,
      "is_returning_champion": true
    },
    {
      "rank": 2,
      "previous_rank": 0,
      "rank_change": 0,
      "user_id": "user-002",
      "user_name": "Jane Smith",
      "avatar_url": "https://cdn.example.com/avatar2.jpg",
      "total_points": 45,
      "round_points": 45,
      "games_played": 1,
      "average_points_per_game": 45.0,
      "highest_score": 45,
      "lowest_score": 45,
      "correct_predictions": 9,
      "total_predictions": 10,
      "prediction_accuracy": 90.0,
      "last_activity_at": "2024-02-10T15:30:00Z",
      "joined_at": "2024-01-01T10:30:45.123Z",
      "is_new_to_league": false,
      "is_returning_champion": false
    }
  ],
  "created_at": "2024-02-10T16:00:00.000Z",
  "updated_at": "2024-02-10T16:30:00.000Z",
  "computed_at": "2024-02-10T16:30:00.000Z"
}
```

### Last Man Standing Standings (Round 5)
```json
{
  "PK": "LEAGUE#league-002",
  "SK": "STANDINGS#LAST_MAN_STANDING#5",
  "GSI1PK": "GAME#game-002",
  "GSI1SK": "STANDINGS#LAST_MAN_STANDING#5",
  "GSI2PK": "STANDINGS_RANK#LAST_MAN_STANDING#1",
  "GSI2SK": "league#league-002#5",
  "entity_type": "STANDINGS",
  "standings_id": "550e8400-e29b-41d4-a716-446655440001",
  "league_id": "league-002",
  "game_id": "game-002",
  "game_type": "LAST_MAN_STANDING",
  "round_number": 5,
  "is_final": false,
  "total_participants": 100,
  "active_participants": 45,
  "eliminated_participants": 55,
  "title": "Week 5 Standings",
  "description": "Current standings after round 5 - 45 players remaining",
  "standings_data": [
    {
      "rank": 1,
      "previous_rank": 1,
      "rank_change": 0,
      "user_id": "user-003",
      "user_name": "Mike Johnson",
      "avatar_url": "https://cdn.example.com/avatar3.jpg",
      "is_alive": true,
      "games_won": 5,
      "games_lost": 0,
      "win_percentage": 100.0,
      "consecutive_wins": 5,
      "consecutive_losses": 0,
      "best_consecutive_wins": 5,
      "lives_remaining": 3,
      "eliminated_round": null,
      "last_activity_at": "2024-02-24T16:00:00Z",
      "joined_at": "2024-01-01T10:30:45.123Z",
      "is_new_to_league": false,
      "is_returning_champion": false
    },
    {
      "rank": 2,
      "previous_rank": 2,
      "rank_change": 0,
      "user_id": "user-004",
      "user_name": "Sarah Williams",
      "avatar_url": "https://cdn.example.com/avatar4.jpg",
      "is_alive": true,
      "games_won": 4,
      "games_lost": 1,
      "win_percentage": 80.0,
      "consecutive_wins": 2,
      "consecutive_losses": 0,
      "best_consecutive_wins": 3,
      "lives_remaining": 2,
      "eliminated_round": null,
      "last_activity_at": "2024-02-24T15:30:00Z",
      "joined_at": "2024-01-01T10:30:45.123Z",
      "is_new_to_league": true,
      "is_returning_champion": false
    },
    {
      "rank": 46,
      "previous_rank": 45,
      "rank_change": -1,
      "user_id": "user-005",
      "user_name": "Tom Brown",
      "avatar_url": "https://cdn.example.com/avatar5.jpg",
      "is_alive": false,
      "games_won": 2,
      "games_lost": 3,
      "win_percentage": 40.0,
      "consecutive_wins": 0,
      "consecutive_losses": 1,
      "best_consecutive_wins": 2,
      "lives_remaining": 0,
      "eliminated_round": 5,
      "last_activity_at": "2024-02-24T14:00:00Z",
      "joined_at": "2024-01-01T10:30:45.123Z",
      "is_new_to_league": false,
      "is_returning_champion": false
    }
  ],
  "created_at": "2024-02-24T16:00:00.000Z",
  "updated_at": "2024-02-24T16:30:00.000Z",
  "computed_at": "2024-02-24T16:30:00.000Z"
}
```

### Final Standings
```json
{
  "PK": "LEAGUE#league-001",
  "SK": "STANDINGS#POINTS_BASED#FINAL",
  "GSI1PK": "GAME#game-001",
  "GSI1SK": "STANDINGS#POINTS_BASED#FINAL",
  "GSI2PK": "STANDINGS_RANK#POINTS_BASED#1",
  "GSI2SK": "league#league-001#FINAL",
  "entity_type": "STANDINGS",
  "standings_id": "550e8400-e29b-41d4-a716-446655440002",
  "league_id": "league-001",
  "game_id": "game-001",
  "game_type": "POINTS_BASED",
  "round_number": 0,
  "is_final": true,
  "total_participants": 50,
  "active_participants": 50,
  "eliminated_participants": 0,
  "title": "Final Standings - Season 2024-25",
  "description": "Final standings after all 38 rounds",
  "is_locked": true,
  "locked_at": "2024-05-31T23:59:59Z",
  "locked_by": "admin-user-id",
  "standings_data": [
    {
      "rank": 1,
      "previous_rank": 1,
      "rank_change": 0,
      "user_id": "user-001",
      "user_name": "John Doe",
      "avatar_url": "https://cdn.example.com/avatar1.jpg",
      "total_points": 1850,
      "round_points": 50,
      "games_played": 38,
      "average_points_per_game": 48.68,
      "highest_score": 60,
      "lowest_score": 30,
      "correct_predictions": 285,
      "total_predictions": 380,
      "prediction_accuracy": 75.0,
      "last_activity_at": "2024-05-31T23:00:00Z",
      "joined_at": "2024-01-01T10:30:45.123Z",
      "is_new_to_league": false,
      "is_returning_champion": true
    }
  ],
  "created_at": "2024-05-31T23:59:59.000Z",
  "updated_at": "2024-05-31T23:59:59.000Z",
  "computed_at": "2024-05-31T23:59:59.000Z"
}
```

---

## Scalability Considerations

### For Millions of Users & Thousands of Leagues

1. **Partition Key Design**
   - `LEAGUE#{league_id}` groups standings by league
   - Enables efficient league-scoped queries
   - Potential hot partition for popular leagues (mitigated by GSI)

2. **Sort Key Design**
   - `STANDINGS#{game_type}#{round_number}` for round standings
   - `STANDINGS#{game_type}#FINAL` for final standings
   - Efficient range queries with `begins_with`

3. **Array Size Management**
   - `standings_data` array can grow large (10,000+ items)
   - Consider pagination for large leagues
   - Use projection expressions to limit data transfer
   - Consider splitting into separate items if > 400KB

4. **DynamoDB Optimization**
   - **Pay-per-request billing**: Scales automatically
   - **Sparse attributes**: Optional fields don't consume capacity
   - **Projection expressions**: Reduce data transfer
   - **Batch operations**: Efficient multi-item reads

5. **Computation Strategy**
   - Use Lambda for async standings computation
   - Trigger on prediction scoring
   - Use DynamoDB Streams for real-time updates
   - Cache computed standings in ElastiCache

6. **Caching Strategy**
   - Cache standings in CloudFront (1 minute TTL)
   - Cache in application layer (30 second TTL)
   - Cache in browser (real-time updates via WebSocket)
   - Invalidate on updates

7. **Monitoring**
   - CloudWatch metrics for read/write capacity
   - X-Ray tracing for slow queries
   - Alarms for throttling and hot partitions
   - DynamoDB Streams for real-time analytics

---

## Integration Points

### With PREDICTION Entity
- Standings computed from predictions
- Points from predictions contribute to standings
- Accuracy stats from predictions

### With ROUND Entity
- Standings updated after round completion
- Round number referenced in standings
- Match results affect standings

### With USER Entity
- User statistics updated from standings
- User rankings from standings
- User achievements from standings

### With LEAGUE Entity
- Standings belong to a league
- League settings affect standings computation
- League members in standings

---

## Computation Algorithm

### Points-Based Standings Computation
```
1. For each user in league:
   a. Get all scored predictions for round
   b. Sum points from predictions
   c. Calculate average points per game
   d. Calculate prediction accuracy
   e. Update user's standing entry

2. Sort users by total_points (descending)

3. Assign ranks (1, 2, 3, ...)

4. Calculate rank_change from previous round

5. Store standings item in DynamoDB
```

### Last Man Standing Standings Computation
```
1. For each user in league:
   a. Get all scored predictions for round
   b. Check if user's prediction was correct
   c. If incorrect, mark as eliminated
   d. Update games_won/games_lost
   e. Update consecutive wins/losses
   f. Update user's standing entry

2. Filter active users (is_alive = true)

3. Sort active users by games_won (descending)

4. Assign ranks to active users

5. Assign ranks to eliminated users (by elimination round)

6. Store standings item in DynamoDB
```

---

## Migration & Backward Compatibility

### Version 1.0 (Current)
- Basic standings metadata
- Points-based and LMS support
- Round and final standings
- User rankings

### Future Enhancements
- **v1.1**: Add standings history/audit trail
- **v1.2**: Add standings analytics (trends, projections)
- **v1.3**: Add live standings updates via WebSocket
- **v2.0**: Add multi-sport support

### Migration Strategy
- Add new attributes as optional (sparse)
- Use feature flags for new functionality
- Gradual rollout to leagues
- Maintain backward compatibility

---

## Security & Privacy

### Data Protection
- All attributes encrypted at rest (DynamoDB encryption)
- HTTPS-only for API access
- User-scoped queries (no cross-league data leakage)
- Standings visible to league members only

### Access Control
- Only system can create/update standings
- Only league members can view standings
- Only admins can lock standings
- Audit trail for all changes

### Audit Trail
- `created_at`, `updated_at` for all items
- `computed_at` for computation timestamp
- `locked_at`, `locked_by` for locking
- CloudWatch Logs for all API access

---

## Cost Optimization

### DynamoDB
- **Pay-per-request**: ~$1.25 per million read units, ~$6.25 per million write units
- **Sparse attributes**: Only pay for data stored
- **Compression**: Consider for large standings_data arrays
- **TTL**: Not applicable (standings are permanent)

### Estimated Monthly Costs (1000 leagues, 50 users each, 10 rounds)
- **Reads**: 50M reads/month = $62.50
- **Writes**: 10M writes/month = $62.50
- **Storage**: 10K standings × 50KB avg = 500MB = $1.25
- **Total**: ~$126/month

### Cost Reduction Strategies
- Archive old standings to S3
- Compress large standings_data arrays
- Use DynamoDB Streams for analytics
- Implement caching layer

---

## Testing Checklist

- [ ] Create standings with all required attributes
- [ ] Create standings with minimal attributes
- [ ] Compute standings from predictions
- [ ] Verify rank calculation
- [ ] Verify rank_change calculation
- [ ] Verify points calculation (points-based)
- [ ] Verify win percentage calculation (LMS)
- [ ] Query league standings
- [ ] Query final standings
- [ ] Query game standings
- [ ] Query user standings
- [ ] Validate standings_data array
- [ ] Test concurrent updates
- [ ] Test batch operations
- [ ] Test GSI queries
- [ ] Test pagination
- [ ] Load test with 1000+ leagues
- [ ] Load test with 10000+ users per league
- [ ] Test standings locking
- [ ] Test standings archival

---

## References

- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Single-Table Design](https://www.alexdebrie.com/posts/dynamodb-single-table/)
- [ISO 8601 - Date/Time Format](https://en.wikipedia.org/wiki/ISO_8601)
- [DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html)
- [DynamoDB Global Secondary Indexes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html)

