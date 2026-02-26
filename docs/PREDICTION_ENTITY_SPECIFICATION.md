# PREDICTION Entity Specification - Multi-Player Fantasy Football Platform

## Overview
The PREDICTION entity represents a user's pick/bet for a specific match within a round. Predictions are the core competitive element, supporting both Points-Based (score prediction) and Last Man Standing (LMS - binary win/loss) competition types. Each prediction is immutable once locked and scored.

## DynamoDB Key Schema

### Primary Keys
```
PK (Partition Key): USER#{user_id}
SK (Sort Key): PREDICTION#{league_id}#{round_number}#{match_id}
```

### Global Secondary Index (GSI1)
```
GSI1PK: LEAGUE#{league_id}
GSI1SK: PREDICTION#{round_number}#{user_id}
```

### Global Secondary Index (GSI2)
```
GSI2PK: MATCH#{match_id}
GSI2SK: PREDICTION#{user_id}
```

### Global Secondary Index (GSI3)
```
GSI3PK: ROUND#{round_number}
GSI3SK: PREDICTION_STATUS#{status}#{user_id}
```

### Access Patterns
1. **Get user's prediction**: `PK=USER#{user_id}, SK=PREDICTION#{league_id}#{round_number}#{match_id}`
2. **Get all user predictions in round**: `PK=USER#{user_id}, SK begins_with PREDICTION#{league_id}#{round_number}#`
3. **Get all user predictions in league**: `PK=USER#{user_id}, SK begins_with PREDICTION#{league_id}#`
4. **Get all predictions for match**: `GSI2PK=MATCH#{match_id}, GSI2SK begins_with PREDICTION#`
5. **Get league predictions for round**: `GSI1PK=LEAGUE#{league_id}, GSI1SK=PREDICTION#{round_number}#{user_id}`
6. **Get round predictions by status**: `GSI3PK=ROUND#{round_number}, GSI3SK begins_with PREDICTION_STATUS#{status}#`

---

## Entity Attributes

### PREDICTION Item (SK=PREDICTION#{league_id}#{round_number}#{match_id})

#### Required Attributes (All Types)

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `PK` | String | Partition key | `USER#user-001` | Format: `USER#{user_id}` |
| `SK` | String | Sort key | `PREDICTION#league-001#1#match-001` | Format: `PREDICTION#{league_id}#{round_number}#{match_id}` |
| `GSI1PK` | String | GSI1 partition key | `LEAGUE#league-001` | Format: `LEAGUE#{league_id}` |
| `GSI1SK` | String | GSI1 sort key | `PREDICTION#1#user-001` | Format: `PREDICTION#{round_number}#{user_id}` |
| `GSI2PK` | String | GSI2 partition key | `MATCH#match-001` | Format: `MATCH#{match_id}` |
| `GSI2SK` | String | GSI2 sort key | `PREDICTION#user-001` | Format: `PREDICTION#{user_id}` |
| `GSI3PK` | String | GSI3 partition key | `ROUND#1` | Format: `ROUND#{round_number}` |
| `GSI3SK` | String | GSI3 sort key | `PREDICTION_STATUS#PENDING#user-001` | Format: `PREDICTION_STATUS#{status}#{user_id}` |
| `entity_type` | String | Entity classification | `PREDICTION` | Fixed value |
| `prediction_id` | String | Unique prediction identifier (UUID v4) | `550e8400-e29b-41d4-a716-446655440000` | Immutable, globally unique |
| `user_id` | String | User making prediction | `user-001` | Reference to USER |
| `league_id` | String | League context | `league-001` | Reference to LEAGUE |
| `game_id` | String | Game context | `game-001` | Reference to GAME |
| `round_id` | String | Round context | `550e8400-e29b-41d4-a716-446655440000` | Reference to ROUND |
| `round_number` | Number | Round number | `1` | Positive integer |
| `match_id` | String | Match being predicted | `match-001` | Reference to ROUND#MATCH |
| `game_type` | String | Competition type | `POINTS_BASED` | POINTS_BASED, LAST_MAN_STANDING |
| `status` | String | Prediction status | `PENDING` | PENDING, LOCKED, SCORED, CANCELLED |
| `home_team` | String | Home team name | `Manchester United` | Max 100 characters |
| `away_team` | String | Away team name | `Liverpool` | Max 100 characters |
| `match_date` | String | Match scheduled date | `2024-02-10T15:00:00Z` | ISO 8601 format |
| `prediction_deadline` | String | Deadline for this prediction | `2024-02-10T14:30:00Z` | ISO 8601 format |
| `created_at` | String | Prediction creation timestamp | `2024-02-09T10:30:45.123Z` | ISO 8601 format, immutable |
| `updated_at` | String | Last update timestamp | `2024-02-09T14:22:10.456Z` | ISO 8601 format |
| `locked_at` | String | When prediction was locked | `2024-02-10T14:30:00Z` | ISO 8601 format |
| `scored_at` | String | When prediction was scored | `2024-02-10T16:00:00Z` | ISO 8601 format |

#### Points-Based Specific Attributes

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `predicted_home_score` | Number | Predicted home team score | `2` | Non-negative integer |
| `predicted_away_score` | Number | Predicted away team score | `1` | Non-negative integer |
| `predicted_result` | String | Predicted match result | `HOME_WIN` | HOME_WIN, AWAY_WIN, DRAW |
| `actual_home_score` | Number | Actual home team score | `2` | Non-negative integer or null |
| `actual_away_score` | Number | Actual away team score | `1` | Non-negative integer or null |
| `actual_result` | String | Actual match result | `HOME_WIN` | HOME_WIN, AWAY_WIN, DRAW, CANCELLED |
| `points_earned` | Number | Points awarded for prediction | `10` | Non-negative integer or null |
| `points_breakdown` | Map | Detailed points calculation | `{"result": 5, "score": 5}` | JSON object |
| `accuracy_type` | String | Type of accuracy achieved | `EXACT_SCORE` | EXACT_SCORE, CORRECT_RESULT, INCORRECT, CANCELLED |

#### Last Man Standing Specific Attributes

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `predicted_winner` | String | Predicted winning team | `HOME` | HOME, AWAY |
| `predicted_winner_id` | String | Predicted winner team ID | `team-001` | External reference |
| `actual_winner` | String | Actual winning team | `HOME` | HOME, AWAY, DRAW, CANCELLED |
| `actual_winner_id` | String | Actual winner team ID | `team-001` | External reference |
| `is_correct` | Boolean | Prediction correct | `true` | True/false or null if not scored |
| `is_alive` | Boolean | User still alive in LMS | `true` | True/false (false if incorrect) |
| `lives_remaining` | Number | Lives remaining (if applicable) | `2` | Non-negative integer |
| `eliminated_round` | Number | Round eliminated (if applicable) | `5` | Positive integer or null |

#### Optional Attributes (All Types)

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `confidence_level` | Number | User confidence (1-10) | `8` | 1-10 integer |
| `reasoning` | String | User's reasoning | `Strong home form` | Max 500 characters |
| `is_locked_early` | Boolean | Locked before deadline | `false` | Default: false |
| `locked_early_at` | String | Early lock timestamp | `2024-02-09T20:00:00Z` | ISO 8601 format |
| `is_edited` | Boolean | Prediction edited | `false` | Default: false |
| `edited_at` | String | Last edit timestamp | `2024-02-09T12:00:00Z` | ISO 8601 format |
| `edit_count` | Number | Number of edits | `1` | Non-negative integer |
| `is_bonus_match` | Boolean | Bonus points match | `false` | Default: false |
| `bonus_multiplier` | Number | Applied bonus multiplier | `1.5` | Positive decimal |
| `notes` | String | Admin notes | `Flagged for review` | Max 500 characters |
| `metadata` | Map | Custom metadata | `{"device": "mobile"}` | JSON object |

---

## Status Transitions

### Prediction Status Lifecycle
```
PENDING → LOCKED → SCORED
   ↓        ↓         ↓
   └────────┴─────────┴─→ CANCELLED (at any point)
```

### Status Definitions
- **PENDING**: Prediction created, can be edited, before deadline
- **LOCKED**: Prediction deadline passed, cannot be edited, awaiting match result
- **SCORED**: Match completed, points calculated, final state
- **CANCELLED**: Prediction cancelled (match cancelled or user removed from league)

### Accuracy Types (Points-Based)
- **EXACT_SCORE**: Predicted exact score (e.g., 2-1)
- **CORRECT_RESULT**: Correct result but wrong score (e.g., predicted 2-1, actual 3-2)
- **INCORRECT**: Wrong result
- **CANCELLED**: Match cancelled, no points awarded

---

## Computed/Derived Fields

These fields are calculated from other attributes and should be computed at query time or cached with TTL.

| Field | Calculation | Update Frequency | Example |
|-------|-----------|------------------|---------|
| `is_locked` | `now >= prediction_deadline` | Real-time | `true` |
| `is_scoreable` | `match_status == COMPLETED` | After match completion | `true` |
| `time_until_deadline` | `(prediction_deadline - now)` | Real-time | `PT30M` |
| `minutes_until_deadline` | `(prediction_deadline - now) / 60` | Real-time | `30` |
| `is_late_prediction` | `created_at > (prediction_deadline - 1 hour)` | Real-time | `false` |
| `prediction_accuracy_percentage` | `(correct_predictions / total_predictions) * 100` | Per user, per league | `63.33` |
| `points_per_prediction` | `total_points / total_predictions` | Per user, per league | `8.5` |

---

## Validation Rules

### Prediction Values
- **Points-Based**: Scores must be non-negative integers
- **LMS**: Winner must be HOME or AWAY
- **Confidence**: 1-10 integer scale
- **Reasoning**: Max 500 characters, no HTML/scripts

### Dates & Times
- ISO 8601 format with millisecond precision
- UTC timezone
- `created_at` must be before `prediction_deadline`
- `locked_at` must be >= `prediction_deadline`
- `scored_at` must be after match completion

### Status Transitions
- PENDING → LOCKED: Automatic at deadline
- LOCKED → SCORED: After match completion
- Any → CANCELLED: Manual or automatic

### Immutability Rules
- `prediction_id` is immutable
- `user_id`, `league_id`, `match_id` are immutable
- `created_at` is immutable
- Predictions cannot be edited after LOCKED status
- Predictions cannot be edited after SCORED status

### Scoring Rules
- Points only awarded when status is SCORED
- Points must be non-negative
- Points breakdown must sum to total points
- Bonus multiplier applied to base points

---

## Constraints & Limits

### Size Constraints
- **Item size**: Max 400 KB per item (DynamoDB limit)
- **Reasoning**: Max 500 characters
- **Notes**: Max 500 characters
- **Metadata**: Max 100 KB

### Rate Limits
- **Prediction creation**: Max 1000 per user per round
- **Prediction updates**: Max 100 per user per round (before locked)
- **Prediction scoring**: Max 10000 per minute per league
- **Batch operations**: Max 25 items per batch

### Data Retention
- **Active predictions**: Indefinite
- **Scored predictions**: Indefinite (historical tracking)
- **Cancelled predictions**: 1 year (then archived)
- **Edit history**: Not stored (only edit_count tracked)

### Concurrent Operations
- Multiple users can predict on same match
- Only user can edit own prediction (before locked)
- Only system can score predictions
- Optimistic locking recommended for updates

---

## Indexes & Query Patterns

### Primary Key Queries
```
# Get user's prediction for match
Query: PK=USER#{user_id}, SK=PREDICTION#{league_id}#{round_number}#{match_id}
Result: Single item
Latency: <10ms

# Get all user predictions in round
Query: PK=USER#{user_id}, SK begins_with PREDICTION#{league_id}#{round_number}#
Result: Multiple items (one per match)
Latency: <50ms

# Get all user predictions in league
Query: PK=USER#{user_id}, SK begins_with PREDICTION#{league_id}#
Result: Multiple items (all rounds)
Latency: <100ms
```

### GSI1 Queries
```
# Get all predictions for league round
Query: GSI1PK=LEAGUE#{league_id}, GSI1SK=PREDICTION#{round_number}#{user_id}
Result: Multiple items (all users' predictions)
Latency: <100ms
```

### GSI2 Queries
```
# Get all predictions for match
Query: GSI2PK=MATCH#{match_id}, GSI2SK begins_with PREDICTION#
Result: Multiple items (all users' predictions)
Latency: <100ms
```

### GSI3 Queries
```
# Get pending predictions for round
Query: GSI3PK=ROUND#{round_number}, GSI3SK begins_with PREDICTION_STATUS#PENDING#
Result: Multiple items (all pending predictions)
Latency: <100ms
```

---

## Example Items

### Points-Based Prediction (PENDING)
```json
{
  "PK": "USER#user-001",
  "SK": "PREDICTION#league-001#1#match-001",
  "GSI1PK": "LEAGUE#league-001",
  "GSI1SK": "PREDICTION#1#user-001",
  "GSI2PK": "MATCH#match-001",
  "GSI2SK": "PREDICTION#user-001",
  "GSI3PK": "ROUND#1",
  "GSI3SK": "PREDICTION_STATUS#PENDING#user-001",
  "entity_type": "PREDICTION",
  "prediction_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-001",
  "league_id": "league-001",
  "game_id": "game-001",
  "round_id": "550e8400-e29b-41d4-a716-446655440001",
  "round_number": 1,
  "match_id": "match-001",
  "game_type": "POINTS_BASED",
  "status": "PENDING",
  "home_team": "Manchester United",
  "away_team": "Liverpool",
  "match_date": "2024-02-10T15:00:00Z",
  "prediction_deadline": "2024-02-10T14:30:00Z",
  "predicted_home_score": 2,
  "predicted_away_score": 1,
  "predicted_result": "HOME_WIN",
  "confidence_level": 8,
  "reasoning": "Manchester United in strong form, Liverpool missing key players",
  "is_locked_early": false,
  "is_edited": false,
  "edit_count": 0,
  "is_bonus_match": false,
  "bonus_multiplier": 1.0,
  "created_at": "2024-02-09T10:30:45.123Z",
  "updated_at": "2024-02-09T14:22:10.456Z"
}
```

### Points-Based Prediction (SCORED)
```json
{
  "PK": "USER#user-001",
  "SK": "PREDICTION#league-001#1#match-001",
  "GSI1PK": "LEAGUE#league-001",
  "GSI1SK": "PREDICTION#1#user-001",
  "GSI2PK": "MATCH#match-001",
  "GSI2SK": "PREDICTION#user-001",
  "GSI3PK": "ROUND#1",
  "GSI3SK": "PREDICTION_STATUS#SCORED#user-001",
  "entity_type": "PREDICTION",
  "prediction_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-001",
  "league_id": "league-001",
  "game_id": "game-001",
  "round_id": "550e8400-e29b-41d4-a716-446655440001",
  "round_number": 1,
  "match_id": "match-001",
  "game_type": "POINTS_BASED",
  "status": "SCORED",
  "home_team": "Manchester United",
  "away_team": "Liverpool",
  "match_date": "2024-02-10T15:00:00Z",
  "prediction_deadline": "2024-02-10T14:30:00Z",
  "predicted_home_score": 2,
  "predicted_away_score": 1,
  "predicted_result": "HOME_WIN",
  "actual_home_score": 2,
  "actual_away_score": 1,
  "actual_result": "HOME_WIN",
  "accuracy_type": "EXACT_SCORE",
  "points_earned": 10,
  "points_breakdown": {
    "result": 5,
    "score": 5
  },
  "confidence_level": 8,
  "reasoning": "Manchester United in strong form, Liverpool missing key players",
  "is_locked_early": false,
  "is_edited": false,
  "edit_count": 0,
  "is_bonus_match": false,
  "bonus_multiplier": 1.0,
  "created_at": "2024-02-09T10:30:45.123Z",
  "updated_at": "2024-02-10T16:00:00.000Z",
  "locked_at": "2024-02-10T14:30:00Z",
  "scored_at": "2024-02-10T16:00:00Z"
}
```

### Last Man Standing Prediction (PENDING)
```json
{
  "PK": "USER#user-002",
  "SK": "PREDICTION#league-002#1#match-001",
  "GSI1PK": "LEAGUE#league-002",
  "GSI1SK": "PREDICTION#1#user-002",
  "GSI2PK": "MATCH#match-001",
  "GSI2SK": "PREDICTION#user-002",
  "GSI3PK": "ROUND#1",
  "GSI3SK": "PREDICTION_STATUS#PENDING#user-002",
  "entity_type": "PREDICTION",
  "prediction_id": "550e8400-e29b-41d4-a716-446655440002",
  "user_id": "user-002",
  "league_id": "league-002",
  "game_id": "game-002",
  "round_id": "550e8400-e29b-41d4-a716-446655440003",
  "round_number": 1,
  "match_id": "match-001",
  "game_type": "LAST_MAN_STANDING",
  "status": "PENDING",
  "home_team": "Manchester United",
  "away_team": "Liverpool",
  "match_date": "2024-02-10T15:00:00Z",
  "prediction_deadline": "2024-02-10T14:30:00Z",
  "predicted_winner": "HOME",
  "predicted_winner_id": "team-001",
  "confidence_level": 7,
  "reasoning": "Home advantage and recent form",
  "is_locked_early": false,
  "is_edited": false,
  "edit_count": 0,
  "created_at": "2024-02-09T10:30:45.123Z",
  "updated_at": "2024-02-09T14:22:10.456Z"
}
```

### Last Man Standing Prediction (SCORED)
```json
{
  "PK": "USER#user-002",
  "SK": "PREDICTION#league-002#1#match-001",
  "GSI1PK": "LEAGUE#league-002",
  "GSI1SK": "PREDICTION#1#user-002",
  "GSI2PK": "MATCH#match-001",
  "GSI2SK": "PREDICTION#user-002",
  "GSI3PK": "ROUND#1",
  "GSI3SK": "PREDICTION_STATUS#SCORED#user-002",
  "entity_type": "PREDICTION",
  "prediction_id": "550e8400-e29b-41d4-a716-446655440002",
  "user_id": "user-002",
  "league_id": "league-002",
  "game_id": "game-002",
  "round_id": "550e8400-e29b-41d4-a716-446655440003",
  "round_number": 1,
  "match_id": "match-001",
  "game_type": "LAST_MAN_STANDING",
  "status": "SCORED",
  "home_team": "Manchester United",
  "away_team": "Liverpool",
  "match_date": "2024-02-10T15:00:00Z",
  "prediction_deadline": "2024-02-10T14:30:00Z",
  "predicted_winner": "HOME",
  "predicted_winner_id": "team-001",
  "actual_winner": "HOME",
  "actual_winner_id": "team-001",
  "is_correct": true,
  "is_alive": true,
  "lives_remaining": 3,
  "confidence_level": 7,
  "reasoning": "Home advantage and recent form",
  "is_locked_early": false,
  "is_edited": false,
  "edit_count": 0,
  "created_at": "2024-02-09T10:30:45.123Z",
  "updated_at": "2024-02-10T16:00:00.000Z",
  "locked_at": "2024-02-10T14:30:00Z",
  "scored_at": "2024-02-10T16:00:00Z"
}
```

---

## Scalability Considerations

### For Millions of Users & Thousands of Leagues

1. **Partition Key Design**
   - `USER#{user_id}` distributes predictions across users
   - Enables efficient user-scoped queries
   - No hot partitions expected

2. **Sort Key Design**
   - `PREDICTION#{league_id}#{round_number}#{match_id}` enables hierarchical queries
   - Efficient range queries with `begins_with`
   - Supports pagination with `ExclusiveStartKey`

3. **GSI Strategy**
   - **GSI1**: Query predictions by league and round
   - **GSI2**: Query predictions by match (for scoring)
   - **GSI3**: Query predictions by status (for batch operations)
   - Enables efficient filtering without full table scans

4. **DynamoDB Optimization**
   - **Pay-per-request billing**: Scales automatically
   - **Sparse attributes**: Optional fields don't consume capacity
   - **Projection expressions**: Reduce data transfer
   - **Batch operations**: Efficient multi-item reads/writes

5. **Scoring Optimization**
   - Use GSI2 to query all predictions for match
   - Batch update predictions after match completion
   - Use DynamoDB Streams for real-time scoring
   - Consider Lambda for async scoring

6. **Caching Strategy**
   - Cache user predictions in application layer (1 minute TTL)
   - Cache match predictions in memory (real-time updates)
   - Cache accuracy stats in browser (5 minute TTL)
   - Invalidate on updates

7. **Monitoring**
   - CloudWatch metrics for read/write capacity
   - X-Ray tracing for slow queries
   - Alarms for throttling and hot partitions
   - DynamoDB Streams for real-time analytics

---

## Integration Points

### With ROUND Entity
- Predictions reference `round_id` and `match_id`
- Prediction deadline must match round's `prediction_deadline`
- Predictions locked when round status becomes LOCKED

### With STANDINGS Entity
- Standings updated after prediction is scored
- Points from predictions contribute to user's total
- Rankings updated in real-time as predictions are scored

### With USER Entity
- Predictions belong to a user
- User statistics updated based on prediction accuracy
- User preferences affect prediction defaults

### With LEAGUE Entity
- Predictions belong to a league
- League settings affect scoring rules
- League members can view/predict on matches

---

## Migration & Backward Compatibility

### Version 1.0 (Current)
- Basic prediction metadata
- Points-based and LMS support
- Status tracking
- Scoring integration

### Future Enhancements
- **v1.1**: Add prediction history/audit trail
- **v1.2**: Add prediction analytics (confidence, accuracy trends)
- **v1.3**: Add live prediction updates via WebSocket
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
- User-scoped queries (no cross-user data leakage)
- Predictions only visible to league members

### Access Control
- Only user can create/edit own predictions (before locked)
- Only system can score predictions
- Only league members can view predictions
- Audit trail for all changes

### Audit Trail
- `created_at`, `updated_at` for all items
- `locked_at`, `scored_at` for status changes
- `edited_at`, `edit_count` for modifications
- CloudWatch Logs for all API access

---

## Cost Optimization

### DynamoDB
- **Pay-per-request**: ~$1.25 per million read units, ~$6.25 per million write units
- **Sparse attributes**: Only pay for data stored
- **Compression**: Consider for large text fields
- **TTL**: Not applicable (predictions are permanent)

### Estimated Monthly Costs (1000 leagues, 100 users each, 10 rounds, 10 matches)
- **Reads**: 100M reads/month = $125
- **Writes**: 10M writes/month = $62.50
- **Storage**: 10M predictions × 2KB avg = 20GB = $5
- **Total**: ~$193/month

### Cost Reduction Strategies
- Archive old predictions to S3
- Compress large text fields
- Use DynamoDB Streams for analytics
- Implement caching layer

---

## Testing Checklist

- [ ] Create prediction with all required attributes
- [ ] Create prediction with minimal attributes
- [ ] Create predictions for multiple matches
- [ ] Update prediction before deadline
- [ ] Verify prediction locks at deadline
- [ ] Score prediction after match completion
- [ ] Calculate points correctly (exact score, correct result, incorrect)
- [ ] Query user's prediction for match
- [ ] Query all user predictions in round
- [ ] Query all predictions for match
- [ ] Query predictions by status
- [ ] Validate date constraints
- [ ] Test concurrent updates
- [ ] Test batch operations
- [ ] Test GSI queries
- [ ] Test pagination
- [ ] Load test with 1M+ predictions
- [ ] Test LMS predictions
- [ ] Test bonus multipliers
- [ ] Test cancellation workflow

---

## References

- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Single-Table Design](https://www.alexdebrie.com/posts/dynamodb-single-table/)
- [ISO 8601 - Date/Time Format](https://en.wikipedia.org/wiki/ISO_8601)
- [DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html)
- [DynamoDB Global Secondary Indexes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html)

