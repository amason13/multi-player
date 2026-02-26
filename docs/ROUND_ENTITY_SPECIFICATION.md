# ROUND Entity Specification - Multi-Player Fantasy Football Platform

## Overview
The ROUND entity represents a weekly period within a game/league where users make predictions and compete. Rounds are the fundamental unit of competition, containing match information, prediction deadlines, and scoring windows. This specification supports both Points-Based and Last Man Standing (LMS) competition types.

## DynamoDB Key Schema

### Primary Keys
```
PK (Partition Key): LEAGUE#{league_id}
SK (Sort Key): ROUND#{round_number} | ROUND#{round_number}#MATCH#{match_id}
```

### Global Secondary Index (GSI1)
```
GSI1PK: GAME#{game_id}
GSI1SK: ROUND#{round_number}
```

### Global Secondary Index (GSI2)
```
GSI2PK: ROUND_STATUS#{status}
GSI2SK: start_date#{start_date}
```

### Access Patterns
1. **Get round details**: `PK=LEAGUE#{league_id}, SK=ROUND#{round_number}`
2. **Get round matches**: `PK=LEAGUE#{league_id}, SK begins_with ROUND#{round_number}#MATCH#`
3. **Get all rounds in league**: `PK=LEAGUE#{league_id}, SK begins_with ROUND#`
4. **Get rounds by game**: `GSI1PK=GAME#{game_id}, GSI1SK=ROUND#{round_number}`
5. **Get active rounds**: `GSI2PK=ROUND_STATUS#ACTIVE, GSI2SK begins_with start_date#`
6. **Get rounds by date range**: `GSI2PK=ROUND_STATUS#{status}, GSI2SK between start_date# and end_date#`

---

## Entity Attributes

### ROUND Item (SK=ROUND#{round_number})

#### Required Attributes

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `PK` | String | Partition key | `LEAGUE#league-001` | Format: `LEAGUE#{league_id}` |
| `SK` | String | Sort key | `ROUND#1` | Format: `ROUND#{round_number}` |
| `GSI1PK` | String | GSI1 partition key | `GAME#game-001` | Format: `GAME#{game_id}` |
| `GSI1SK` | String | GSI1 sort key | `ROUND#1` | Format: `ROUND#{round_number}` |
| `GSI2PK` | String | GSI2 partition key | `ROUND_STATUS#ACTIVE` | Format: `ROUND_STATUS#{status}` |
| `GSI2SK` | String | GSI2 sort key | `start_date#2024-02-10T00:00:00Z` | Format: `start_date#{ISO8601}` |
| `entity_type` | String | Entity classification | `ROUND` | Fixed value |
| `round_id` | String | Unique round identifier (UUID v4) | `550e8400-e29b-41d4-a716-446655440000` | Immutable, globally unique |
| `league_id` | String | Parent league identifier | `league-001` | Reference to LEAGUE |
| `game_id` | String | Parent game identifier | `game-001` | Reference to GAME |
| `round_number` | Number | Sequential round number | `1` | Positive integer, unique per league |
| `status` | String | Round status | `ACTIVE` | SCHEDULED, ACTIVE, LOCKED, COMPLETED, CANCELLED |
| `start_date` | String | Round start date/time | `2024-02-10T00:00:00Z` | ISO 8601 format, UTC |
| `end_date` | String | Round end date/time | `2024-02-17T23:59:59Z` | ISO 8601 format, UTC |
| `prediction_deadline` | String | Deadline for predictions | `2024-02-10T12:00:00Z` | ISO 8601 format, UTC |
| `scoring_start_date` | String | When scoring begins | `2024-02-10T15:00:00Z` | ISO 8601 format, UTC |
| `scoring_end_date` | String | When scoring ends | `2024-02-17T23:59:59Z` | ISO 8601 format, UTC |
| `match_count` | Number | Total matches in round | `10` | Non-negative integer |
| `game_type` | String | Competition type | `POINTS_BASED` | POINTS_BASED, LAST_MAN_STANDING |
| `created_at` | String | Round creation timestamp | `2024-01-15T10:30:45.123Z` | ISO 8601 format, immutable |
| `updated_at` | String | Last update timestamp | `2024-02-09T14:22:10.456Z` | ISO 8601 format, auto-updated |

#### Optional Attributes

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `title` | String | Round display title | `Week 1: Premier League Matchday 1` | Max 200 characters |
| `description` | String | Round description | `First week of the season` | Max 1000 characters |
| `theme` | String | Round theme/category | `PREMIER_LEAGUE` | Max 50 characters |
| `featured_match_id` | String | Featured/highlighted match | `match-001` | Reference to match |
| `total_predictions` | Number | Total predictions made | `1250` | Non-negative integer |
| `completed_predictions` | Number | Completed predictions | `1200` | Non-negative integer |
| `prediction_completion_rate` | Number | Completion percentage | `96.0` | 0-100, 2 decimal places |
| `is_playoff_round` | Boolean | Is this a playoff round | `false` | Default: false |
| `is_final_round` | Boolean | Is this the final round | `false` | Default: false |
| `playoff_tier` | Number | Playoff tier level | `1` | Positive integer or null |
| `notes` | String | Admin notes | `Delayed due to weather` | Max 500 characters |
| `cancelled_reason` | String | Reason for cancellation | `Technical issues` | Max 500 characters, if cancelled |
| `cancelled_at` | String | Cancellation timestamp | `2024-02-10T08:00:00Z` | ISO 8601 format |
| `cancelled_by` | String | User who cancelled | `admin-user-id` | User ID |
| `metadata` | Map | Custom metadata | `{"sport": "football", "league": "PL"}` | JSON object |

---

### ROUND#MATCH Item (SK=ROUND#{round_number}#MATCH#{match_id})

Stores individual match information within a round. Multiple items per round.

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `PK` | String | Partition key | `LEAGUE#league-001` | Format: `LEAGUE#{league_id}` |
| `SK` | String | Sort key | `ROUND#1#MATCH#match-001` | Format: `ROUND#{round_number}#MATCH#{match_id}` |
| `entity_type` | String | Entity classification | `ROUND_MATCH` | Fixed value |
| `match_id` | String | Unique match identifier | `match-001` | UUID v4 |
| `round_id` | String | Parent round identifier | `550e8400-e29b-41d4-a716-446655440000` | Reference to ROUND |
| `league_id` | String | Parent league identifier | `league-001` | Reference to LEAGUE |
| `round_number` | Number | Round number | `1` | Positive integer |
| `match_number` | Number | Match sequence in round | `1` | Positive integer |
| `home_team` | String | Home team name | `Manchester United` | Max 100 characters |
| `away_team` | String | Away team name | `Liverpool` | Max 100 characters |
| `home_team_id` | String | Home team external ID | `team-001` | External reference |
| `away_team_id` | String | Away team external ID | `team-002` | External reference |
| `match_date` | String | Scheduled match date/time | `2024-02-10T15:00:00Z` | ISO 8601 format, UTC |
| `match_status` | String | Match status | `SCHEDULED` | SCHEDULED, LIVE, COMPLETED, POSTPONED, CANCELLED |
| `home_score` | Number | Home team final score | `2` | Non-negative integer or null |
| `away_score` | Number | Away team final score | `1` | Non-negative integer or null |
| `result` | String | Match result | `HOME_WIN` | HOME_WIN, AWAY_WIN, DRAW, PENDING, CANCELLED |
| `prediction_count` | Number | Total predictions for match | `500` | Non-negative integer |
| `prediction_deadline` | String | Prediction deadline | `2024-02-10T14:30:00Z` | ISO 8601 format, UTC |
| `is_featured` | Boolean | Is featured match | `true` | Default: false |
| `is_bonus_match` | Boolean | Bonus points match | `false` | Default: false |
| `bonus_multiplier` | Number | Points multiplier | `1.5` | Positive decimal, default: 1.0 |
| `venue` | String | Match venue | `Old Trafford` | Max 200 characters |
| `referee` | String | Match referee | `Mike Dean` | Max 100 characters |
| `attendance` | Number | Match attendance | `75000` | Non-negative integer |
| `created_at` | String | Creation timestamp | `2024-01-15T10:30:45.123Z` | ISO 8601 format |
| `updated_at` | String | Last update timestamp | `2024-02-10T16:00:00.000Z` | ISO 8601 format |

---

## Computed/Derived Fields

These fields are calculated from other attributes and should be computed at query time or cached with TTL.

| Field | Calculation | Update Frequency | Example |
|-------|-----------|------------------|---------|
| `prediction_completion_rate` | `(completed_predictions / total_predictions) * 100` | After each prediction | `96.0` |
| `is_active` | `now >= start_date AND now <= end_date` | Real-time | `true` |
| `is_locked` | `now >= prediction_deadline` | Real-time | `true` |
| `is_scoreable` | `now >= scoring_start_date AND now <= scoring_end_date` | Real-time | `true` |
| `days_until_start` | `(start_date - now) / 86400` | Real-time | `2` |
| `days_until_deadline` | `(prediction_deadline - now) / 86400` | Real-time | `0.5` |
| `days_until_end` | `(end_date - now) / 86400` | Real-time | `7` |
| `match_status_summary` | `Count of matches by status` | After each match update | `{"COMPLETED": 8, "LIVE": 2}` |
| `round_progress_percentage` | `(completed_matches / total_matches) * 100` | After each match | `80.0` |

---

## Status Transitions

### Round Status Lifecycle
```
SCHEDULED → ACTIVE → LOCKED → COMPLETED
    ↓         ↓        ↓          ↓
    └─────────┴────────┴──────────┴─→ CANCELLED (at any point)
```

### Status Definitions
- **SCHEDULED**: Round created, predictions not yet open
- **ACTIVE**: Predictions open, matches not yet started
- **LOCKED**: Predictions closed, matches in progress or completed
- **COMPLETED**: All matches finished, final scores recorded
- **CANCELLED**: Round cancelled, no scoring

### Match Status Lifecycle
```
SCHEDULED → LIVE → COMPLETED
    ↓        ↓         ↓
    └────────┴─────────┴─→ POSTPONED (at any point)
    └────────┴─────────┴─→ CANCELLED (at any point)
```

---

## Validation Rules

### Round Number
- Positive integer
- Unique per league
- Sequential (no gaps)
- Immutable after creation

### Dates & Times
- ISO 8601 format with millisecond precision
- UTC timezone
- `start_date` < `prediction_deadline` < `end_date`
- `scoring_start_date` <= `scoring_end_date`
- All dates in future (except for completed rounds)

### Match Count
- Non-negative integer
- Must match actual number of ROUND#MATCH items
- Validated on round creation

### Scores
- Non-negative integers
- Only set when match is COMPLETED
- Home score and away score must both be set or both be null

### Result
- Valid values: HOME_WIN, AWAY_WIN, DRAW, PENDING, CANCELLED
- Derived from scores when match completes
- PENDING if match not yet completed
- CANCELLED if match cancelled

### Prediction Deadline
- Must be before match start date
- Typically 30-60 minutes before match
- Cannot be changed after round is ACTIVE

### Bonus Multiplier
- Positive decimal (e.g., 1.5, 2.0)
- Default: 1.0
- Max: 5.0

### Title & Description
- Title: 1-200 characters
- Description: 0-1000 characters
- No HTML/script tags allowed

---

## Constraints & Limits

### Size Constraints
- **Item size**: Max 400 KB per item (DynamoDB limit)
- **Title**: Max 200 characters
- **Description**: Max 1000 characters
- **Notes**: Max 500 characters
- **Metadata**: Max 100 KB

### Rate Limits
- **Round creation**: Max 100 per league per day
- **Round updates**: Max 1000 per minute per league
- **Match updates**: Max 10000 per minute per league
- **Status changes**: Max 10 per minute per round

### Data Retention
- **Active rounds**: Indefinite
- **Completed rounds**: Indefinite (historical tracking)
- **Cancelled rounds**: 1 year (then archived)
- **Match data**: Indefinite

### Concurrent Operations
- Multiple users can view same round
- Only admin can update round
- Only system can update match scores
- Optimistic locking recommended for updates

---

## Indexes & Query Patterns

### Primary Key Queries
```
# Get round details
Query: PK=LEAGUE#{league_id}, SK=ROUND#{round_number}
Result: Single item
Latency: <10ms

# Get all matches in round
Query: PK=LEAGUE#{league_id}, SK begins_with ROUND#{round_number}#MATCH#
Result: Multiple items (one per match)
Latency: <50ms

# Get all rounds in league
Query: PK=LEAGUE#{league_id}, SK begins_with ROUND#
Result: Multiple items (one per round + matches)
Latency: <100ms
```

### GSI1 Queries
```
# Get all rounds in game
Query: GSI1PK=GAME#{game_id}, GSI1SK begins_with ROUND#
Result: Multiple items (one per round)
Latency: <50ms
```

### GSI2 Queries
```
# Get active rounds
Query: GSI2PK=ROUND_STATUS#ACTIVE, GSI2SK begins_with start_date#
Result: Multiple items (all active rounds)
Latency: <100ms

# Get rounds by date range
Query: GSI2PK=ROUND_STATUS#{status}, GSI2SK between start_date#2024-02-01 and start_date#2024-02-28
Result: Multiple items (rounds in date range)
Latency: <100ms
```

---

## Example Items

### ROUND Item
```json
{
  "PK": "LEAGUE#league-001",
  "SK": "ROUND#1",
  "GSI1PK": "GAME#game-001",
  "GSI1SK": "ROUND#1",
  "GSI2PK": "ROUND_STATUS#ACTIVE",
  "GSI2SK": "start_date#2024-02-10T00:00:00Z",
  "entity_type": "ROUND",
  "round_id": "550e8400-e29b-41d4-a716-446655440000",
  "league_id": "league-001",
  "game_id": "game-001",
  "round_number": 1,
  "status": "ACTIVE",
  "start_date": "2024-02-10T00:00:00Z",
  "end_date": "2024-02-17T23:59:59Z",
  "prediction_deadline": "2024-02-10T12:00:00Z",
  "scoring_start_date": "2024-02-10T15:00:00Z",
  "scoring_end_date": "2024-02-17T23:59:59Z",
  "match_count": 10,
  "game_type": "POINTS_BASED",
  "title": "Week 1: Premier League Matchday 1",
  "description": "First week of the 2024-25 season",
  "theme": "PREMIER_LEAGUE",
  "total_predictions": 1250,
  "completed_predictions": 1200,
  "prediction_completion_rate": 96.0,
  "is_playoff_round": false,
  "is_final_round": false,
  "created_at": "2024-01-15T10:30:45.123Z",
  "updated_at": "2024-02-09T14:22:10.456Z"
}
```

### ROUND#MATCH Item
```json
{
  "PK": "LEAGUE#league-001",
  "SK": "ROUND#1#MATCH#match-001",
  "entity_type": "ROUND_MATCH",
  "match_id": "match-001",
  "round_id": "550e8400-e29b-41d4-a716-446655440000",
  "league_id": "league-001",
  "round_number": 1,
  "match_number": 1,
  "home_team": "Manchester United",
  "away_team": "Liverpool",
  "home_team_id": "team-001",
  "away_team_id": "team-002",
  "match_date": "2024-02-10T15:00:00Z",
  "match_status": "COMPLETED",
  "home_score": 2,
  "away_score": 1,
  "result": "HOME_WIN",
  "prediction_count": 500,
  "prediction_deadline": "2024-02-10T14:30:00Z",
  "is_featured": true,
  "is_bonus_match": false,
  "bonus_multiplier": 1.0,
  "venue": "Old Trafford",
  "referee": "Mike Dean",
  "attendance": 75000,
  "created_at": "2024-01-15T10:30:45.123Z",
  "updated_at": "2024-02-10T16:00:00.000Z"
}
```

---

## Scalability Considerations

### For Millions of Users & Thousands of Leagues

1. **Partition Key Design**
   - `LEAGUE#{league_id}` groups all round data together
   - Enables efficient league-scoped queries
   - Potential hot partition for popular leagues (mitigated by GSI)

2. **Sort Key Design**
   - `ROUND#{round_number}` for round metadata
   - `ROUND#{round_number}#MATCH#{match_id}` for matches
   - Efficient range queries with `begins_with`
   - Supports pagination with `ExclusiveStartKey`

3. **GSI Strategy**
   - **GSI1**: Query rounds by game (cross-league queries)
   - **GSI2**: Query rounds by status and date (time-based queries)
   - Enables efficient filtering without full table scans

4. **DynamoDB Optimization**
   - **Pay-per-request billing**: Scales automatically
   - **Sparse attributes**: Optional fields don't consume capacity
   - **Projection expressions**: Reduce data transfer
   - **Batch operations**: Efficient multi-item reads

5. **Hot Partition Mitigation**
   - Use GSI2 for status/date queries instead of scanning PK
   - Implement caching for frequently accessed rounds
   - Consider write sharding for high-volume updates

6. **Caching Strategy**
   - Cache round metadata in CloudFront (5 minute TTL)
   - Cache match data in application layer (1 minute TTL)
   - Cache status in browser (real-time updates via WebSocket)
   - Invalidate on updates

7. **Monitoring**
   - CloudWatch metrics for read/write capacity
   - X-Ray tracing for slow queries
   - Alarms for throttling and hot partitions
   - DynamoDB Streams for real-time updates

---

## Integration Points

### With PREDICTION Entity
- Predictions reference `round_id` and `match_id`
- Prediction deadline must match round's `prediction_deadline`
- Predictions locked when round status becomes LOCKED

### With STANDINGS Entity
- Standings updated after round completion
- Points calculated based on match results
- Rankings updated in real-time as matches complete

### With LEAGUE Entity
- Round belongs to a league
- League settings affect round configuration
- League members can view/predict on rounds

### With GAME Entity
- Round belongs to a game
- Game type (POINTS_BASED vs LMS) affects scoring
- Game settings affect round behavior

---

## Migration & Backward Compatibility

### Version 1.0 (Current)
- Basic round metadata
- Match information
- Status tracking
- Support for both game types

### Future Enhancements
- **v1.1**: Add round-level bonuses/multipliers
- **v1.2**: Add weather/injury data integration
- **v1.3**: Add live score updates via WebSocket
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
- Admin-only updates for round configuration

### Access Control
- Only league members can view rounds
- Only league admins can create/update rounds
- Only system can update match scores
- Audit trail for all changes

### Audit Trail
- `created_at`, `updated_at` for all items
- `cancelled_at`, `cancelled_by` for cancellations
- CloudWatch Logs for all API access
- DynamoDB Streams for change tracking

---

## Cost Optimization

### DynamoDB
- **Pay-per-request**: ~$1.25 per million read units, ~$6.25 per million write units
- **Sparse attributes**: Only pay for data stored
- **Compression**: Consider for large text fields
- **TTL**: Not applicable (rounds are permanent)

### Estimated Monthly Costs (1000 leagues, 10 rounds each)
- **Reads**: 10M reads/month = $12.50
- **Writes**: 1M writes/month = $6.25
- **Storage**: 10K rounds × 5KB avg = 50MB = $0.12
- **Total**: ~$19/month

### Cost Reduction Strategies
- Archive old rounds to S3
- Compress large text fields
- Use DynamoDB Streams for analytics
- Implement caching layer

---

## Testing Checklist

- [ ] Create round with all required attributes
- [ ] Create round with minimal attributes
- [ ] Create multiple matches in round
- [ ] Update round status (SCHEDULED → ACTIVE → LOCKED → COMPLETED)
- [ ] Update match score and verify result calculation
- [ ] Query round by league and round number
- [ ] Query all matches in round
- [ ] Query all rounds in league
- [ ] Query rounds by game
- [ ] Query active rounds by date
- [ ] Validate date constraints (start < deadline < end)
- [ ] Validate match count matches actual items
- [ ] Test concurrent updates
- [ ] Test batch operations
- [ ] Test GSI queries
- [ ] Test pagination
- [ ] Load test with 1000+ rounds
- [ ] Load test with 10000+ matches
- [ ] Test cancellation workflow
- [ ] Test status transitions

---

## References

- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Single-Table Design](https://www.alexdebrie.com/posts/dynamodb-single-table/)
- [ISO 8601 - Date/Time Format](https://en.wikipedia.org/wiki/ISO_8601)
- [DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html)
- [DynamoDB Global Secondary Indexes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html)

