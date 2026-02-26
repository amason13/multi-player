# Entity Specifications Summary - Multi-Player Fantasy Football Platform

## Overview

This document provides a comprehensive summary of all entity specifications for the Multi-Player fantasy football/tipping competition platform. The platform supports both Points-Based and Last Man Standing (LMS) competition types with hierarchical data modeling in DynamoDB.

## Entity Specifications

### 1. USER Entity
**File**: `USER_ENTITY_SPECIFICATION.md`
**Lines**: 545
**Purpose**: Represents registered users with profiles, preferences, settings, and statistics

#### Key Components
- **PROFILE**: User identity and basic information
- **PREFERENCES**: User feature toggles and notification settings
- **SETTINGS**: Account security and configuration
- **STATISTICS**: Per-league aggregated statistics

#### Key Attributes
- User ID (UUID v4)
- Email (unique, immutable)
- Profile visibility and privacy controls
- Account status (ACTIVE, SUSPENDED, DELETED)
- Per-league statistics (points, rankings, accuracy)

#### Access Patterns
- Get user profile by ID
- Get user preferences
- Get user settings
- Get user statistics by league
- Get all user statistics

#### Scalability
- Supports millions of users
- Efficient user-scoped queries
- No hot partitions expected
- Pay-per-request billing

---

### 2. ROUND Entity
**File**: `ROUND_ENTITY_SPECIFICATION.md`
**Lines**: 527
**Purpose**: Represents weekly competition periods with matches and prediction deadlines

#### Key Components
- **ROUND**: Round metadata and configuration
- **ROUND#MATCH**: Individual match information within round

#### Key Attributes
- Round number (sequential per league)
- Status (SCHEDULED, ACTIVE, LOCKED, COMPLETED, CANCELLED)
- Prediction deadline
- Scoring window
- Match count and details
- Support for both game types

#### Access Patterns
- Get round details
- Get round matches
- Get all rounds in league
- Get rounds by game
- Get active rounds by date
- Get rounds by status

#### Scalability
- Supports thousands of leagues
- Efficient league-scoped queries
- GSI for cross-league queries
- Handles 10,000+ matches per league

---

### 3. PREDICTION Entity
**File**: `PREDICTION_ENTITY_SPECIFICATION.md`
**Lines**: 614
**Purpose**: Represents user predictions/picks for matches with scoring and accuracy tracking

#### Key Components
- **PREDICTION**: User's prediction for a specific match

#### Key Attributes
- **Points-Based**: Predicted scores, result, accuracy type, points earned
- **LMS**: Predicted winner, correctness, alive status, lives remaining
- Status (PENDING, LOCKED, SCORED, CANCELLED)
- Confidence level and reasoning
- Edit tracking and early lock support

#### Access Patterns
- Get user's prediction for match
- Get all user predictions in round
- Get all user predictions in league
- Get all predictions for match
- Get league predictions for round
- Get round predictions by status

#### Scalability
- Supports millions of predictions
- Efficient user-scoped queries
- GSI for match-based queries
- Handles 10M+ predictions per league

---

### 4. STANDINGS Entity
**File**: `STANDINGS_ENTITY_SPECIFICATION.md`
**Lines**: 704
**Purpose**: Represents leaderboards and rankings computed from predictions and match results

#### Key Components
- **STANDINGS**: Aggregated standings with player rankings
- **STANDINGS_DATA**: Array of player standing entries

#### Key Attributes
- Game type (POINTS_BASED, LAST_MAN_STANDING)
- Round number or FINAL
- Total/active/eliminated participant counts
- Player rankings with detailed statistics
- Computation and lock timestamps

#### Access Patterns
- Get league standings for round
- Get final standings
- Get game standings
- Get user's ranking
- Get top players by rank
- Get standings by status

#### Scalability
- Supports thousands of leagues
- Efficient league-scoped queries
- Handles 10,000+ players per league
- Real-time computation via Lambda

---

## DynamoDB Single-Table Design

### Key Schema Overview

```
Primary Keys:
- USER#{user_id} / PROFILE | PREFERENCES | SETTINGS | STATISTICS#{league_id}
- LEAGUE#{league_id} / ROUND#{round_number} | ROUND#{round_number}#MATCH#{match_id}
- LEAGUE#{league_id} / STANDINGS#{game_type}#{round_number}
- USER#{user_id} / PREDICTION#{league_id}#{round_number}#{match_id}

Global Secondary Indexes:
- GSI1: Cross-entity queries (USER→LEAGUE, GAME→ROUND, etc.)
- GSI2: Status and date-based queries
- GSI3: User-centric queries across entities
```

### Entity Relationships

```
LEAGUE
├── ROUND (multiple per league)
│   ├── ROUND#MATCH (multiple per round)
│   └── STANDINGS (one per game_type per round)
│       └── STANDINGS_DATA (array of player entries)
│
USER
├── PROFILE
├── PREFERENCES
├── SETTINGS
├── STATISTICS (one per league)
└── PREDICTION (multiple per league per round)
    └── References ROUND#MATCH
```

---

## Validation Rules Summary

### Common Validation Rules

| Rule | Applies To | Details |
|------|-----------|---------|
| **UUID v4 Format** | user_id, round_id, prediction_id, standings_id | Immutable, globally unique |
| **ISO 8601 Dates** | All timestamps | UTC timezone, millisecond precision |
| **Non-negative Integers** | Points, scores, counts, ranks | >= 0 |
| **Percentages** | Accuracy, win %, etc. | 0-100, 2 decimal places |
| **Email Format** | User email | RFC 5322, unique, immutable |
| **Status Enums** | All status fields | Predefined values only |
| **Immutability** | created_at, user_id, league_id | Cannot be changed after creation |

### Entity-Specific Rules

#### USER
- Email: Unique, max 254 characters
- Name: 1-100 characters, no leading/trailing whitespace
- Country: ISO 3166-1 alpha-2 (2 chars)
- Language: ISO 639-1 (2 chars)
- Timezone: IANA format
- Account status transitions: ACTIVE → SUSPENDED → ACTIVE or DELETED

#### ROUND
- Round number: Sequential, no gaps, unique per league
- Dates: start_date < prediction_deadline < end_date
- Match count: Must match actual ROUND#MATCH items
- Scores: Non-negative, both set or both null
- Result: Derived from scores (HOME_WIN, AWAY_WIN, DRAW, PENDING, CANCELLED)

#### PREDICTION
- Scores (Points-Based): Non-negative integers
- Winner (LMS): HOME or AWAY
- Confidence: 1-10 integer
- Status transitions: PENDING → LOCKED → SCORED (or CANCELLED)
- Immutability: Cannot edit after LOCKED status
- Dates: created_at < prediction_deadline < locked_at < scored_at

#### STANDINGS
- Rank: Positive integer, unique per standings, sequential
- Points: Non-negative, total >= round
- Win percentage: 0-100, 2 decimal places
- Participant counts: total >= active, active + eliminated = total
- standings_data: Max 10,000 items per standings

---

## Computed/Derived Fields

### USER Statistics
- `rank_change`: previous_rank - current_rank
- `win_percentage`: (games_won / games_played) * 100
- `average_points_per_game`: total_points / games_played
- `prediction_accuracy`: (correct_predictions / total_predictions) * 100

### ROUND
- `prediction_completion_rate`: (completed_predictions / total_predictions) * 100
- `is_active`: now >= start_date AND now <= end_date
- `is_locked`: now >= prediction_deadline
- `days_until_deadline`: (prediction_deadline - now) / 86400

### PREDICTION
- `is_locked`: now >= prediction_deadline
- `is_scoreable`: match_status == COMPLETED
- `time_until_deadline`: prediction_deadline - now
- `prediction_accuracy_percentage`: (correct_predictions / total_predictions) * 100

### STANDINGS
- `rank_change`: previous_rank - current_rank
- `active_participants`: Count of users with is_alive=true
- `eliminated_participants`: Count of users with is_alive=false
- `standings_complete`: active_participants == 0 OR round_number == final

---

## Status Transitions

### USER Account Status
```
ACTIVE ←→ SUSPENDED → DELETED
```

### ROUND Status
```
SCHEDULED → ACTIVE → LOCKED → COMPLETED
    ↓         ↓        ↓          ↓
    └─────────┴────────┴──────────┴─→ CANCELLED
```

### PREDICTION Status
```
PENDING → LOCKED → SCORED
   ↓        ↓         ↓
   └────────┴─────────┴─→ CANCELLED
```

### STANDINGS Status
```
COMPUTING → PUBLISHED → LOCKED → ARCHIVED
```

---

## Constraints & Limits

### Size Constraints
| Entity | Constraint | Details |
|--------|-----------|---------|
| Item | 400 KB max | DynamoDB limit |
| Attribute | 400 KB max | DynamoDB limit |
| standings_data | 10,000 items max | Per standings |
| Text fields | 500-1000 chars | Varies by field |

### Rate Limits
| Operation | Limit | Details |
|-----------|-------|---------|
| User creation | 1000/min | Per system |
| Prediction creation | 1000/min | Per user per round |
| Standings updates | 10000/min | Per league |
| Batch operations | 25 items | Per batch |

### Data Retention
| Data | Retention | Details |
|------|-----------|---------|
| Active records | Indefinite | Permanent storage |
| Deleted records | 90 days | Then purged |
| Archived records | Indefinite | Read-only |
| Logs | 1 year | CloudWatch retention |

---

## Query Performance

### Expected Latencies
| Query Type | Latency | Details |
|-----------|---------|---------|
| Get single item | <10ms | Primary key query |
| Query by PK | <50ms | Range query |
| GSI query | <50-100ms | Secondary index |
| Scan | O(n) | Avoid in production |

### Optimization Strategies
1. **Use projection expressions** to reduce data transfer
2. **Batch operations** for multiple items
3. **Pagination** for large result sets
4. **Caching** for frequently accessed data
5. **GSI** for inverted queries
6. **Avoid scans** in production

---

## Cost Estimation

### Monthly Costs (1000 leagues, 100 users each, 10 rounds, 10 matches)

| Component | Reads | Writes | Storage | Cost |
|-----------|-------|--------|---------|------|
| USER | 10M | 1M | 500MB | $15 |
| ROUND | 5M | 500K | 50MB | $7 |
| PREDICTION | 100M | 10M | 20GB | $193 |
| STANDINGS | 50M | 5M | 500MB | $63 |
| **Total** | **165M** | **16.5M** | **21GB** | **$278** |

### Cost Optimization
- Archive old data to S3
- Compress large text fields
- Use DynamoDB Streams for analytics
- Implement caching layer
- Use on-demand billing

---

## Security & Privacy

### Data Protection
- ✅ Encryption at rest (DynamoDB)
- ✅ HTTPS-only API access
- ✅ User-scoped queries
- ✅ Sensitive data in Cognito only

### Access Control
- ✅ Cognito authentication
- ✅ User-scoped authorization
- ✅ Admin-only operations
- ✅ Audit trails

### Privacy Controls
- ✅ Profile visibility settings
- ✅ Granular data sharing
- ✅ Data export capability
- ✅ Account deletion (30-day grace)

---

## Integration Points

### Entity Dependencies
```
LEAGUE
  ├── ROUND (contains matches)
  │   ├── PREDICTION (user picks)
  │   └── STANDINGS (computed from predictions)
  │
  └── USER (league members)
      ├── PREDICTION (user's picks)
      └── STATISTICS (aggregated from predictions)
```

### Data Flow
```
1. User creates PREDICTION for ROUND#MATCH
2. ROUND status changes to LOCKED at deadline
3. ROUND#MATCH completes with result
4. PREDICTION is SCORED with points
5. STANDINGS computed from all predictions
6. USER STATISTICS updated from standings
```

---

## Testing Checklist

### USER Entity
- [ ] Create user with all attributes
- [ ] Create user with minimal attributes
- [ ] Update profile/preferences/settings
- [ ] Query user by ID
- [ ] Query user statistics by league
- [ ] Validate email format
- [ ] Test account status transitions
- [ ] Test concurrent updates

### ROUND Entity
- [ ] Create round with matches
- [ ] Update round status
- [ ] Update match scores
- [ ] Query round by league
- [ ] Query matches in round
- [ ] Validate date constraints
- [ ] Test status transitions
- [ ] Load test with 10K+ matches

### PREDICTION Entity
- [ ] Create prediction (points-based)
- [ ] Create prediction (LMS)
- [ ] Update prediction before deadline
- [ ] Verify prediction locks
- [ ] Score prediction
- [ ] Calculate points correctly
- [ ] Query user predictions
- [ ] Load test with 1M+ predictions

### STANDINGS Entity
- [ ] Compute standings from predictions
- [ ] Verify rank calculation
- [ ] Verify points calculation
- [ ] Query league standings
- [ ] Query final standings
- [ ] Test standings locking
- [ ] Load test with 10K+ users

---

## Migration & Versioning

### Current Version
- **Version**: 1.0
- **Status**: Production Ready
- **Last Updated**: 2024-02-26

### Future Enhancements
- **v1.1**: Add prediction history/audit trail
- **v1.2**: Add standings analytics and projections
- **v1.3**: Add live updates via WebSocket
- **v2.0**: Add multi-sport support

### Migration Strategy
- Add new attributes as optional (sparse)
- Use feature flags for new functionality
- Gradual rollout to users
- Maintain backward compatibility

---

## References

### AWS Documentation
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Single-Table Design](https://www.alexdebrie.com/posts/dynamodb-single-table/)
- [Global Secondary Indexes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html)
- [DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html)

### Standards
- [ISO 8601 - Date/Time Format](https://en.wikipedia.org/wiki/ISO_8601)
- [RFC 5322 - Email Format](https://tools.ietf.org/html/rfc5322)
- [IANA Timezone Database](https://www.iana.org/time-zones)
- [ISO 639-1 Language Codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
- [ISO 3166-1 Country Codes](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)

---

## Document Index

| Document | Lines | Purpose |
|----------|-------|---------|
| USER_ENTITY_SPECIFICATION.md | 545 | User profiles, preferences, settings, statistics |
| ROUND_ENTITY_SPECIFICATION.md | 527 | Weekly competition periods and matches |
| PREDICTION_ENTITY_SPECIFICATION.md | 614 | User predictions with scoring |
| STANDINGS_ENTITY_SPECIFICATION.md | 704 | Leaderboards and rankings |
| ENTITY_SPECIFICATIONS_SUMMARY.md | This | Overview and cross-entity reference |
| **Total** | **2,990** | **Comprehensive entity documentation** |

---

## Quick Reference

### Create Operations
```
USER: Create profile, preferences, settings
ROUND: Create round with matches
PREDICTION: Create prediction for match
STANDINGS: Compute from predictions
```

### Read Operations
```
USER: Get profile, preferences, settings, statistics
ROUND: Get round details, matches
PREDICTION: Get user predictions, match predictions
STANDINGS: Get league standings, user ranking
```

### Update Operations
```
USER: Update profile, preferences, settings
ROUND: Update status, match scores
PREDICTION: Edit before deadline, score after match
STANDINGS: Recompute after predictions scored
```

### Delete Operations
```
USER: Soft delete (mark as DELETED)
ROUND: Cancel round
PREDICTION: Cancel prediction
STANDINGS: Archive old standings
```

---

## Support & Questions

For questions about these specifications:
1. Review the detailed specification document
2. Check the examples section
3. Review the validation rules
4. Consult the testing checklist
5. Refer to AWS documentation

---

**Last Updated**: 2024-02-26
**Version**: 1.0
**Status**: Production Ready
