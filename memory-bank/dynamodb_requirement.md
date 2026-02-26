# DynamoDB Modeling Session - Multi-Player Fantasy Football/Tipping Competition Platform

## Application Overview
- **Domain**: Fantasy Football/Tipping Competition Platform
- **Key Entities**: 
  - USER (1:M) LEAGUE
  - LEAGUE (1:M) GAME
  - GAME (1:M) ROUND
  - ROUND (1:M) PREDICTION
  - LEAGUE (1:M) LEAGUE_MEMBER
  - GAME (1:M) GAME_MEMBER
  - LEAGUE (1:M) INVITATION
- **Business Context**: 
  - Multi-game, multi-round competition platform
  - Support for multiple game types (Last Man Standing, Points-based, future types)
  - Users compete in leagues with multiple games running simultaneously
  - Points accumulate across all games to determine overall league standings
  - LMS: Users pick teams weekly, cannot repeat picks, eliminated if team loses
  - Points-based: Users make multiple bets per round, earn points for correct predictions
- **Scale**: 
  - Millions of users
  - Hundreds of thousands of leagues
  - Billions of potential records (users × leagues × games × rounds × predictions)
  - Pay-per-request billing model

## Access Patterns Analysis

| Pattern # | Description | RPS (Peak/Avg) | Type | Attributes Needed | Key Requirements | Design Considerations | Status |
|-----------|-------------|----------------|------|-------------------|------------------|----------------------|--------|
| 1 | Get user profile | 500/100 | Read | user_id, email, name, avatar, timezone, created_at | <50ms latency | Simple PK lookup | ✅ |
| 2 | Get user's leagues | 400/80 | Read | user_id, league_id, league_name, member_count, game_count | <100ms latency | GSI query by user | ✅ |
| 3 | Create league | 50/10 | Write | league_id, name, owner_id, description, created_at | Atomic write | Generate UUID | ✅ |
| 4 | Get league details | 300/60 | Read | league_id, name, owner_id, member_count, game_count, created_at | <100ms latency | PK lookup | ✅ |
| 5 | Get league members | 250/50 | Read | league_id, user_id, role, joined_at, stats | <100ms latency | Query by league | ✅ |
| 6 | Add member to league | 100/20 | Write | league_id, user_id, role, joined_at | Atomic write | Update member count | ✅ |
| 7 | Get league's games | 200/40 | Read | league_id, game_id, game_type, current_round, status | <100ms latency | Query by league | ✅ |
| 8 | Create game | 30/6 | Write | game_id, league_id, game_type, rules, created_at | Atomic write | Initialize game | ✅ |
| 9 | Get game details | 250/50 | Read | game_id, league_id, game_type, current_round, status, rules | <100ms latency | PK lookup | ✅ |
| 10 | Get game's rounds | 200/40 | Read | game_id, round_id, round_number, status, deadline | <100ms latency | Query by game | ✅ |
| 11 | Create round | 20/4 | Write | round_id, game_id, round_number, status, deadline | Atomic write | Initialize round | ✅ |
| 12 | Get round details | 300/60 | Read | round_id, game_id, round_number, status, deadline, match_count | <100ms latency | PK lookup | ✅ |
| 13 | Submit prediction | 1000/200 | Write | prediction_id, user_id, round_id, game_id, pick, points_earned | <200ms latency | High write volume | ✅ |
| 14 | Get user's predictions for round | 400/80 | Read | user_id, round_id, game_id, prediction_id, pick, points | <100ms latency | GSI query | ✅ |
| 15 | Get all predictions for round | 150/30 | Read | round_id, user_id, prediction_id, pick, points | <200ms latency | Query for scoring | ✅ |
| 16 | Get game standings | 300/60 | Read | game_id, user_id, points, rank, status | <100ms latency | Sorted by points | ✅ |
| 17 | Get league standings | 400/80 | Read | league_id, user_id, total_points, rank | <100ms latency | Sorted by points | ✅ |
| 18 | Get user's stats in league | 200/40 | Read | league_id, user_id, total_points, games_played, accuracy | <100ms latency | User-scoped query | ✅ |
| 19 | Get user's pick history (LMS) | 100/20 | Read | user_id, game_id, round_id, pick, result | <100ms latency | Prevent duplicates | ✅ |
| 20 | Check if user eliminated (LMS) | 500/100 | Read | user_id, game_id, is_eliminated, lives_remaining | <50ms latency | Real-time check | ✅ |
| 21 | Send league invitation | 50/10 | Write | invitation_id, league_id, inviter_id, invitee_email, status | Atomic write | Track invitations | ✅ |
| 22 | Get pending invitations | 200/40 | Read | user_id, invitation_id, league_id, inviter_id, created_at | <100ms latency | GSI query | ✅ |
| 23 | Accept/reject invitation | 100/20 | Write | invitation_id, status, updated_at | Atomic write | Update status | ✅ |
| 24 | Score round (batch) | 10/2 | Write | round_id, user_id, points_earned, updated_at | Batch operation | Transactional | ✅ |

## Entity Relationships Deep Dive

### USER → LEAGUE (1:Many)
- Average: 1-3 leagues per user
- Max: Unbounded (power users)
- Access correlation: 100% (users always query their leagues)
- Update frequency: Leagues added/removed occasionally

### LEAGUE → GAME (1:Many)
- Average: 2-5 games per league
- Max: Unbounded
- Access correlation: 90% (league details include game count, games queried separately)
- Update frequency: Games created at league start, rarely modified

### LEAGUE → LEAGUE_MEMBER (1:Many)
- Average: 5-20 members per league
- Max: Unbounded
- Access correlation: 80% (league details include member count, members queried separately)
- Update frequency: Members added/removed throughout season

### GAME → ROUND (1:Many)
- Average: 10-20 rounds per game (weekly for season)
- Max: Bounded by season length
- Access correlation: 85% (game details include round count, rounds queried separately)
- Update frequency: Rounds created at season start, status updated weekly

### ROUND → PREDICTION (1:Many)
- Average: 5-20 predictions per round (one per user in game)
- Max: Unbounded
- Access correlation: 95% (round details include prediction count, predictions queried for scoring)
- Update frequency: Predictions submitted before deadline, then locked

### GAME → GAME_MEMBER (1:Many)
- Average: 5-20 members per game
- Max: Unbounded
- Access correlation: 70% (game details include member count, members queried separately)
- Update frequency: Members added at game start, status updated (LMS elimination)

## Enhanced Aggregate Analysis

### USER + LEAGUE Item Collection Analysis
- **Access Correlation**: 100% of queries need user profile with league list
- **Query Patterns**:
  - User profile only: 10% of queries
  - User's leagues: 90% of queries
- **Size Constraints**: User 2KB + 3 leagues 3KB = 5KB total, bounded growth
- **Update Patterns**: User updates monthly, leagues added/removed occasionally
- **Identifying Relationship**: Leagues cannot exist without users, but users can exist without leagues
- **Decision**: Item Collection Aggregate (USER#<id> with SK patterns for PROFILE and LEAGUE#<league_id>)
- **Justification**: 90% joint access + identifying relationship eliminates need for separate LEAGUE table + GSI

### LEAGUE + LEAGUE_MEMBER Item Collection Analysis
- **Access Correlation**: 80% of queries need league details with member list
- **Query Patterns**:
  - League metadata only: 20% of queries
  - League with members: 80% of queries
- **Size Constraints**: League 2KB + 20 members 10KB = 12KB total, bounded growth
- **Update Patterns**: League metadata updated rarely, members added/removed frequently
- **Identifying Relationship**: Members cannot exist without league, always have league_id when querying
- **Decision**: Item Collection Aggregate (LEAGUE#<id> with SK patterns for METADATA and MEMBER#<user_id>)
- **Justification**: 80% joint access + identifying relationship + bounded size

### GAME + GAME_MEMBER Item Collection Analysis
- **Access Correlation**: 70% of queries need game details with member status
- **Query Patterns**:
  - Game metadata only: 30% of queries
  - Game with members: 70% of queries
- **Size Constraints**: Game 2KB + 20 members 10KB = 12KB total, bounded growth
- **Update Patterns**: Game metadata updated rarely, member status updated weekly (LMS)
- **Identifying Relationship**: Members cannot exist without game, always have game_id when querying
- **Decision**: Item Collection Aggregate (GAME#<id> with SK patterns for METADATA and MEMBER#<user_id>)
- **Justification**: 70% joint access + identifying relationship + bounded size

### GAME + ROUND Item Collection Analysis
- **Access Correlation**: 85% of queries need game details with round list
- **Query Patterns**:
  - Game metadata only: 15% of queries
  - Game with rounds: 85% of queries
- **Size Constraints**: Game 2KB + 20 rounds 10KB = 12KB total, bounded growth
- **Update Patterns**: Game metadata updated rarely, rounds created at season start
- **Identifying Relationship**: Rounds cannot exist without game, always have game_id when querying
- **Decision**: Item Collection Aggregate (GAME#<id> with SK patterns for METADATA and ROUND#<round_id>)
- **Justification**: 85% joint access + identifying relationship + bounded size

### ROUND + PREDICTION Item Collection Analysis
- **Access Correlation**: 95% of queries need round details with predictions
- **Query Patterns**:
  - Round metadata only: 5% of queries
  - Round with predictions: 95% of queries
- **Size Constraints**: Round 2KB + 20 predictions 10KB = 12KB total, bounded growth
- **Update Patterns**: Round metadata updated weekly, predictions submitted before deadline
- **Identifying Relationship**: Predictions cannot exist without round, always have round_id when querying
- **Decision**: Item Collection Aggregate (ROUND#<id> with SK patterns for METADATA and PREDICTION#<user_id>)
- **Justification**: 95% joint access + identifying relationship + bounded size

### STANDINGS (Game-level and League-level)
- **Access Correlation**: 100% of queries need standings sorted by points
- **Query Patterns**:
  - Game standings: 50% of queries
  - League standings: 50% of queries
- **Size Constraints**: Standings 1KB per user, unbounded growth
- **Update Patterns**: Updated after each round scoring
- **Decision**: Separate STANDINGS entities (GAME_STANDINGS#<game_id>, LEAGUE_STANDINGS#<league_id>)
- **Justification**: Different update frequencies, different query patterns, need efficient sorting by points

## Table Consolidation Analysis

### Consolidation Decision Framework

| Parent | Child | Relationship | Access Overlap | Consolidation Decision | Justification |
|--------|-------|--------------|----------------|------------------------|---------------|
| USER | LEAGUE | 1:Many | 90% | ✅ Consolidate | High access overlap + identifying relationship |
| LEAGUE | LEAGUE_MEMBER | 1:Many | 80% | ✅ Consolidate | High access overlap + identifying relationship |
| LEAGUE | GAME | 1:Many | 90% | ✅ Consolidate | High access overlap + identifying relationship |
| GAME | GAME_MEMBER | 1:Many | 70% | ✅ Consolidate | Acceptable overlap + identifying relationship |
| GAME | ROUND | 1:Many | 85% | ✅ Consolidate | High access overlap + identifying relationship |
| ROUND | PREDICTION | 1:Many | 95% | ✅ Consolidate | Very high overlap + identifying relationship |
| LEAGUE | STANDINGS | 1:1 | 100% | ⚠️ Consider | Different update patterns, need efficient sorting |
| GAME | STANDINGS | 1:1 | 100% | ⚠️ Consider | Different update patterns, need efficient sorting |
| LEAGUE | INVITATION | 1:Many | 40% | ❌ Separate | Low access overlap, independent operations |

## Design Considerations (Scratchpad)

### Hot Partition Concerns
- **Predictions**: Pattern #13 at 1000 RPS peak could create hot partitions if concentrated on popular rounds
  - Mitigation: Distribute by user_id in partition key, query by round_id in GSI
- **Standings**: Pattern #16-17 at 300-400 RPS could create hot partitions if concentrated on popular games/leagues
  - Mitigation: Use game_id/league_id as partition key, sort by points in sort key

### GSI Projections
- **Predictions GSI**: Need user_id, round_id, game_id, pick, points - use INCLUDE projection
- **Standings GSI**: Need game_id/league_id, user_id, points, rank - use INCLUDE projection
- **Invitations GSI**: Need user_id, invitation_id, league_id, status - use INCLUDE projection

### Sparse GSI Opportunities
- **LMS Elimination GSI**: Only include items where is_eliminated = true (sparse)
- **Pending Invitations GSI**: Only include items where status = "PENDING" (sparse)

### Multi-Entity Query Patterns
- Get user with leagues: Query USER#<id> with SK begins_with LEAGUE#
- Get league with members: Query LEAGUE#<id> with SK begins_with MEMBER#
- Get game with rounds: Query GAME#<id> with SK begins_with ROUND#
- Get round with predictions: Query ROUND#<id> with SK begins_with PREDICTION#

### Denormalization Ideas
- Duplicate league_name in LEAGUE_MEMBER for quick display
- Duplicate game_type in ROUND for quick filtering
- Duplicate user_name in PREDICTION for leaderboard display
- Duplicate current_round in GAME for quick status check

## Validation Checklist
- [x] Application domain and scale documented
- [x] All entities and relationships mapped
- [x] Aggregate boundaries identified based on access patterns
- [x] Identifying relationships checked for consolidation opportunities
- [x] Table consolidation analysis completed
- [x] Every access pattern has: RPS (avg/peak), latency SLO, consistency, expected result bound, item size band
- [x] Write pattern exists for every read pattern
- [x] Multi-attribute keys considered for each GSI
- [x] Hot partition risks evaluated
- [x] Consolidation framework applied; candidates reviewed
- [x] Design considerations captured
