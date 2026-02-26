# USER Entity Specification - Multi-Player Fantasy Football Platform

## Overview
The USER entity represents a registered user in the Multi-Player platform. It stores user identity, profile information, preferences, settings, and aggregated statistics across all leagues. This specification is designed to support millions of users at scale with efficient DynamoDB queries.

## DynamoDB Key Schema

### Primary Keys
```
PK (Partition Key): USER#{user_id}
SK (Sort Key): PROFILE | PREFERENCES | SETTINGS | STATISTICS#{league_id}
```

### Global Secondary Index (GSI1)
```
GSI1PK: USER#{user_id}
GSI1SK: LEAGUE#{league_id} | STAT#{league_id}
```

### Access Patterns
1. **Get user profile**: `PK=USER#{user_id}, SK=PROFILE`
2. **Get user preferences**: `PK=USER#{user_id}, SK=PREFERENCES`
3. **Get user settings**: `PK=USER#{user_id}, SK=SETTINGS`
4. **Get user statistics**: `PK=USER#{user_id}, SK begins_with STATISTICS#`
5. **Get league-specific stats**: `GSI1PK=USER#{user_id}, GSI1SK=STAT#{league_id}`

---

## Entity Attributes

### PROFILE Item (SK=PROFILE)

#### Required Attributes

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `PK` | String | Partition key | `USER#550e8400-e29b-41d4-a716-446655440000` | Format: `USER#{uuid}` |
| `SK` | String | Sort key | `PROFILE` | Fixed value |
| `entity_type` | String | Entity classification | `USER` | Fixed value |
| `user_id` | String | Unique user identifier (UUID v4) | `550e8400-e29b-41d4-a716-446655440000` | Immutable, globally unique |
| `email` | String | User email address | `john.doe@example.com` | Immutable, unique, validated |
| `email_verified` | Boolean | Email verification status | `true` | Set by Cognito |
| `name` | String | User's display name | `John Doe` | 1-100 characters |
| `created_at` | String | Account creation timestamp | `2024-01-15T10:30:45.123Z` | ISO 8601 format, immutable |
| `updated_at` | String | Last profile update timestamp | `2024-01-20T14:22:10.456Z` | ISO 8601 format, auto-updated |

#### Optional Attributes

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `avatar_url` | String | User profile picture URL | `https://cdn.example.com/avatars/user123.jpg` | HTTPS URL, max 500 chars |
| `bio` | String | User biography/description | `Fantasy football enthusiast` | Max 500 characters |
| `phone_number` | String | User phone number | `+1-555-123-4567` | E.164 format, optional |
| `country` | String | User country code | `US` | ISO 3166-1 alpha-2 |
| `timezone` | String | User timezone | `America/New_York` | IANA timezone format |
| `preferred_language` | String | User language preference | `en` | ISO 639-1 code |
| `date_of_birth` | String | User birth date | `1990-05-15` | ISO 8601 date format |
| `account_status` | String | Account state | `ACTIVE` | ACTIVE, SUSPENDED, DELETED |
| `last_login_at` | String | Last login timestamp | `2024-01-20T14:22:10.456Z` | ISO 8601 format |
| `login_count` | Number | Total login count | `42` | Non-negative integer |
| `cognito_sub` | String | Cognito subject identifier | `550e8400-e29b-41d4-a716-446655440000` | Immutable, from Cognito |

---

### PREFERENCES Item (SK=PREFERENCES)

Stores user-specific preferences and feature toggles.

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `PK` | String | Partition key | `USER#550e8400-e29b-41d4-a716-446655440000` | Format: `USER#{uuid}` |
| `SK` | String | Sort key | `PREFERENCES` | Fixed value |
| `entity_type` | String | Entity classification | `USER_PREFERENCES` | Fixed value |
| `email_notifications_enabled` | Boolean | Email notification opt-in | `true` | Default: true |
| `push_notifications_enabled` | Boolean | Push notification opt-in | `true` | Default: true |
| `sms_notifications_enabled` | Boolean | SMS notification opt-in | `false` | Default: false |
| `marketing_emails_enabled` | Boolean | Marketing email opt-in | `false` | Default: false |
| `league_invites_enabled` | Boolean | Allow league invitations | `true` | Default: true |
| `friend_requests_enabled` | Boolean | Allow friend requests | `true` | Default: true |
| `profile_visibility` | String | Profile visibility level | `PUBLIC` | PUBLIC, FRIENDS_ONLY, PRIVATE |
| `show_real_name` | Boolean | Display real name in leagues | `true` | Default: true |
| `show_email` | Boolean | Display email publicly | `false` | Default: false |
| `show_statistics` | Boolean | Display statistics publicly | `true` | Default: true |
| `theme_preference` | String | UI theme preference | `DARK` | LIGHT, DARK, AUTO |
| `notification_frequency` | String | Notification frequency | `DAILY` | INSTANT, HOURLY, DAILY, WEEKLY |
| `preferred_game_type` | String | Preferred competition type | `POINTS_BASED` | POINTS_BASED, LAST_MAN_STANDING, BOTH |
| `auto_join_leagues` | Boolean | Auto-join public leagues | `false` | Default: false |
| `updated_at` | String | Last preference update | `2024-01-20T14:22:10.456Z` | ISO 8601 format |

---

### SETTINGS Item (SK=SETTINGS)

Stores user account settings and configurations.

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `PK` | String | Partition key | `USER#550e8400-e29b-41d4-a716-446655440000` | Format: `USER#{uuid}` |
| `SK` | String | Sort key | `SETTINGS` | Fixed value |
| `entity_type` | String | Entity classification | `USER_SETTINGS` | Fixed value |
| `two_factor_enabled` | Boolean | 2FA status | `true` | Default: false |
| `two_factor_method` | String | 2FA method | `TOTP` | TOTP, SMS, EMAIL |
| `password_changed_at` | String | Last password change | `2024-01-10T08:15:30.000Z` | ISO 8601 format |
| `password_expiry_days` | Number | Days until password expires | `90` | Positive integer or null |
| `session_timeout_minutes` | Number | Session timeout duration | `30` | Positive integer, default: 30 |
| `ip_whitelist` | List | Allowed IP addresses | `["192.168.1.1", "10.0.0.0/8"]` | CIDR notation allowed |
| `ip_whitelist_enabled` | Boolean | Enable IP whitelist | `false` | Default: false |
| `api_keys_enabled` | Boolean | Allow API key generation | `true` | Default: false |
| `data_export_enabled` | Boolean | Allow data export | `true` | Default: true |
| `account_deletion_requested` | Boolean | Account deletion pending | `false` | Default: false |
| `account_deletion_date` | String | Scheduled deletion date | `2024-02-20T00:00:00.000Z` | ISO 8601 format, 30 days from request |
| `updated_at` | String | Last settings update | `2024-01-20T14:22:10.456Z` | ISO 8601 format |

---

### STATISTICS Item (SK=STATISTICS#{league_id})

Stores aggregated user statistics per league. Multiple items exist per user (one per league).

| Attribute | Type | Description | Example | Constraints |
|-----------|------|-------------|---------|-------------|
| `PK` | String | Partition key | `USER#550e8400-e29b-41d4-a716-446655440000` | Format: `USER#{uuid}` |
| `SK` | String | Sort key | `STATISTICS#league-id-123` | Format: `STATISTICS#{league_id}` |
| `GSI1PK` | String | GSI1 partition key | `USER#550e8400-e29b-41d4-a716-446655440000` | Format: `USER#{user_id}` |
| `GSI1SK` | String | GSI1 sort key | `STAT#league-id-123` | Format: `STAT#{league_id}` |
| `entity_type` | String | Entity classification | `USER_STATISTICS` | Fixed value |
| `user_id` | String | User identifier | `550e8400-e29b-41d4-a716-446655440000` | Reference to user |
| `league_id` | String | League identifier | `league-id-123` | Reference to league |
| `game_type` | String | Competition type | `POINTS_BASED` | POINTS_BASED, LAST_MAN_STANDING |
| `total_points` | Number | Total points earned | `1250` | Non-negative integer |
| `current_rank` | Number | Current league ranking | `3` | Positive integer |
| `previous_rank` | Number | Previous week ranking | `5` | Positive integer |
| `rank_change` | Number | Rank change (positive = improvement) | `2` | Integer (can be negative) |
| `games_played` | Number | Total games/rounds played | `15` | Non-negative integer |
| `games_won` | Number | Games won (LMS) | `8` | Non-negative integer |
| `games_lost` | Number | Games lost (LMS) | `7` | Non-negative integer |
| `win_percentage` | Number | Win percentage (LMS) | `53.33` | 0-100, 2 decimal places |
| `average_points_per_game` | Number | Average points per game | `83.33` | Non-negative, 2 decimal places |
| `highest_score` | Number | Highest single-game score | `150` | Non-negative integer |
| `lowest_score` | Number | Lowest single-game score | `45` | Non-negative integer |
| `consecutive_wins` | Number | Current win streak | `3` | Non-negative integer |
| `consecutive_losses` | Number | Current loss streak | `0` | Non-negative integer |
| `best_consecutive_wins` | Number | Best win streak ever | `7` | Non-negative integer |
| `total_predictions` | Number | Total predictions made | `150` | Non-negative integer |
| `correct_predictions` | Number | Correct predictions | `95` | Non-negative integer |
| `prediction_accuracy` | Number | Prediction accuracy % | `63.33` | 0-100, 2 decimal places |
| `joined_at` | String | League join date | `2024-01-01T10:30:45.123Z` | ISO 8601 format |
| `last_activity_at` | String | Last activity in league | `2024-01-20T14:22:10.456Z` | ISO 8601 format |
| `updated_at` | String | Last statistics update | `2024-01-20T14:22:10.456Z` | ISO 8601 format |

---

## Computed/Derived Fields

These fields are calculated from other attributes and should be computed at query time or cached with TTL.

| Field | Calculation | Update Frequency | Example |
|-------|-----------|------------------|---------|
| `rank_change` | `previous_rank - current_rank` | After each round | `2` |
| `win_percentage` | `(games_won / games_played) * 100` | After each game | `53.33` |
| `average_points_per_game` | `total_points / games_played` | After each game | `83.33` |
| `prediction_accuracy` | `(correct_predictions / total_predictions) * 100` | After each prediction | `63.33` |
| `is_active` | `last_activity_at > (now - 30 days)` | Real-time | `true` |
| `days_since_last_login` | `(now - last_login_at) / 86400` | Real-time | `2` |
| `account_age_days` | `(now - created_at) / 86400` | Real-time | `365` |

---

## Validation Rules

### Email
- Must be valid email format (RFC 5322)
- Must be unique across all users
- Case-insensitive for uniqueness
- Max 254 characters

### Name
- Required, 1-100 characters
- Alphanumeric, spaces, hyphens, apostrophes allowed
- No leading/trailing whitespace

### User ID
- UUID v4 format
- Immutable
- Globally unique
- Generated at account creation

### Timestamps
- ISO 8601 format with millisecond precision
- UTC timezone
- `created_at` is immutable
- `updated_at` auto-updated on any modification

### Statistics
- All numeric fields must be non-negative
- Percentages: 0-100 with max 2 decimal places
- Rank: positive integer
- Rank change: can be negative

### Account Status
- Valid values: `ACTIVE`, `SUSPENDED`, `DELETED`
- Default: `ACTIVE`
- Transitions: ACTIVE → SUSPENDED → ACTIVE or DELETED

### Timezone
- Must be valid IANA timezone identifier
- Examples: `America/New_York`, `Europe/London`, `Asia/Tokyo`

### Language
- ISO 639-1 code (2 characters)
- Examples: `en`, `es`, `fr`, `de`

### Country
- ISO 3166-1 alpha-2 code (2 characters)
- Examples: `US`, `GB`, `CA`, `AU`

---

## Constraints & Limits

### Size Constraints
- **Item size**: Max 400 KB per item (DynamoDB limit)
- **Attribute name**: Max 64 KB
- **Attribute value**: Max 400 KB
- **Email**: Max 254 characters
- **Name**: Max 100 characters
- **Bio**: Max 500 characters
- **Avatar URL**: Max 500 characters

### Rate Limits
- **Profile updates**: Max 10 per minute per user
- **Settings changes**: Max 5 per minute per user
- **Preference updates**: Max 10 per minute per user
- **Statistics updates**: Automatic, no manual limit

### Data Retention
- **Active accounts**: Indefinite
- **Deleted accounts**: 90 days (then purged)
- **Suspended accounts**: Indefinite (until reactivated)
- **Login history**: 1 year (archived)
- **Statistics**: Indefinite (historical tracking)

---

## Indexes & Query Patterns

### Primary Key Queries
```
# Get user profile
Query: PK=USER#{user_id}, SK=PROFILE
Result: Single item
Latency: <10ms

# Get all user data
Query: PK=USER#{user_id}
Result: Multiple items (PROFILE, PREFERENCES, SETTINGS, STATISTICS#*)
Latency: <50ms
```

### GSI1 Queries
```
# Get user's league statistics
Query: GSI1PK=USER#{user_id}, GSI1SK begins_with STAT#
Result: Multiple items (one per league)
Latency: <50ms
```

### Scan Operations (Avoid in Production)
```
# Find users by email (requires secondary index or scan)
Scan: Filter email = "user@example.com"
Latency: O(n) - expensive, avoid
```

---

## Example Items

### PROFILE Item
```json
{
  "PK": "USER#550e8400-e29b-41d4-a716-446655440000",
  "SK": "PROFILE",
  "entity_type": "USER",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "email_verified": true,
  "name": "John Doe",
  "avatar_url": "https://cdn.example.com/avatars/user123.jpg",
  "bio": "Fantasy football enthusiast and data analyst",
  "phone_number": "+1-555-123-4567",
  "country": "US",
  "timezone": "America/New_York",
  "preferred_language": "en",
  "date_of_birth": "1990-05-15",
  "account_status": "ACTIVE",
  "last_login_at": "2024-01-20T14:22:10.456Z",
  "login_count": 42,
  "cognito_sub": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-01T10:30:45.123Z",
  "updated_at": "2024-01-20T14:22:10.456Z"
}
```

### PREFERENCES Item
```json
{
  "PK": "USER#550e8400-e29b-41d4-a716-446655440000",
  "SK": "PREFERENCES",
  "entity_type": "USER_PREFERENCES",
  "email_notifications_enabled": true,
  "push_notifications_enabled": true,
  "sms_notifications_enabled": false,
  "marketing_emails_enabled": false,
  "league_invites_enabled": true,
  "friend_requests_enabled": true,
  "profile_visibility": "PUBLIC",
  "show_real_name": true,
  "show_email": false,
  "show_statistics": true,
  "theme_preference": "DARK",
  "notification_frequency": "DAILY",
  "preferred_game_type": "POINTS_BASED",
  "auto_join_leagues": false,
  "updated_at": "2024-01-20T14:22:10.456Z"
}
```

### SETTINGS Item
```json
{
  "PK": "USER#550e8400-e29b-41d4-a716-446655440000",
  "SK": "SETTINGS",
  "entity_type": "USER_SETTINGS",
  "two_factor_enabled": true,
  "two_factor_method": "TOTP",
  "password_changed_at": "2024-01-10T08:15:30.000Z",
  "password_expiry_days": 90,
  "session_timeout_minutes": 30,
  "ip_whitelist": ["192.168.1.1", "10.0.0.0/8"],
  "ip_whitelist_enabled": false,
  "api_keys_enabled": true,
  "data_export_enabled": true,
  "account_deletion_requested": false,
  "updated_at": "2024-01-20T14:22:10.456Z"
}
```

### STATISTICS Item (Points-Based)
```json
{
  "PK": "USER#550e8400-e29b-41d4-a716-446655440000",
  "SK": "STATISTICS#league-001",
  "GSI1PK": "USER#550e8400-e29b-41d4-a716-446655440000",
  "GSI1SK": "STAT#league-001",
  "entity_type": "USER_STATISTICS",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "league_id": "league-001",
  "game_type": "POINTS_BASED",
  "total_points": 1250,
  "current_rank": 3,
  "previous_rank": 5,
  "rank_change": 2,
  "games_played": 15,
  "average_points_per_game": 83.33,
  "highest_score": 150,
  "lowest_score": 45,
  "total_predictions": 150,
  "correct_predictions": 95,
  "prediction_accuracy": 63.33,
  "joined_at": "2024-01-01T10:30:45.123Z",
  "last_activity_at": "2024-01-20T14:22:10.456Z",
  "updated_at": "2024-01-20T14:22:10.456Z"
}
```

### STATISTICS Item (Last Man Standing)
```json
{
  "PK": "USER#550e8400-e29b-41d4-a716-446655440000",
  "SK": "STATISTICS#league-002",
  "GSI1PK": "USER#550e8400-e29b-41d4-a716-446655440000",
  "GSI1SK": "STAT#league-002",
  "entity_type": "USER_STATISTICS",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "league_id": "league-002",
  "game_type": "LAST_MAN_STANDING",
  "current_rank": 1,
  "previous_rank": 2,
  "rank_change": 1,
  "games_played": 12,
  "games_won": 10,
  "games_lost": 2,
  "win_percentage": 83.33,
  "consecutive_wins": 5,
  "consecutive_losses": 0,
  "best_consecutive_wins": 8,
  "joined_at": "2024-01-05T14:30:00.000Z",
  "last_activity_at": "2024-01-20T14:22:10.456Z",
  "updated_at": "2024-01-20T14:22:10.456Z"
}
```

---

## Scalability Considerations

### For Millions of Users

1. **Partition Key Design**
   - `USER#{uuid}` ensures even distribution across partitions
   - UUIDs provide natural randomization
   - No hot partitions expected

2. **Sort Key Design**
   - Multiple items per user (PROFILE, PREFERENCES, SETTINGS, STATISTICS#*)
   - Efficient batch reads with `begins_with` queries
   - Supports pagination with `ExclusiveStartKey`

3. **DynamoDB Optimization**
   - **Pay-per-request billing**: Scales automatically with demand
   - **Sparse attributes**: Optional fields don't consume capacity
   - **TTL**: Can be used for temporary data (e.g., deleted accounts)
   - **Streams**: Enable real-time updates and analytics

4. **Query Optimization**
   - Use GSI1 for inverted queries (find leagues by user)
   - Batch operations for multiple items
   - Projection expressions to reduce data transfer
   - Consistent reads only when necessary

5. **Caching Strategy**
   - Cache user profile in CloudFront (1 hour TTL)
   - Cache statistics in application layer (5 minute TTL)
   - Cache preferences in browser localStorage
   - Invalidate on updates

6. **Monitoring**
   - CloudWatch metrics for read/write capacity
   - X-Ray tracing for slow queries
   - DynamoDB Streams for real-time analytics
   - Alarms for throttling and errors

---

## Migration & Backward Compatibility

### Version 1.0 (Current)
- Basic profile, preferences, settings
- Per-league statistics
- Support for both game types

### Future Enhancements
- **v1.1**: Add social features (friends, followers)
- **v1.2**: Add achievement/badge system
- **v1.3**: Add prediction history tracking
- **v2.0**: Add mobile app support (additional attributes)

### Migration Strategy
- Add new attributes as optional (sparse)
- Use feature flags for new functionality
- Gradual rollout to users
- Maintain backward compatibility

---

## Security & Privacy

### Data Protection
- All attributes encrypted at rest (DynamoDB encryption)
- HTTPS-only for API access
- User-scoped queries (no cross-user data leakage)
- Sensitive fields (password) stored in Cognito only

### Privacy Controls
- `profile_visibility` controls public access
- `show_email`, `show_real_name` for granular control
- `data_export_enabled` for GDPR compliance
- Account deletion with 30-day grace period

### Audit Trail
- `created_at`, `updated_at` for all items
- `last_login_at` for security monitoring
- `password_changed_at` for compliance
- CloudWatch Logs for all API access

---

## Cost Optimization

### DynamoDB
- **Pay-per-request**: ~$1.25 per million read units, ~$6.25 per million write units
- **Sparse attributes**: Only pay for data stored
- **Compression**: Consider for large text fields
- **TTL**: Automatic cleanup of deleted accounts

### Estimated Monthly Costs (1M users)
- **Reads**: 100M reads/month = $125
- **Writes**: 10M writes/month = $62.50
- **Storage**: 1M users × 5KB avg = 5GB = $1.25
- **Total**: ~$190/month

### Cost Reduction Strategies
- Archive old statistics to S3
- Compress large text fields
- Use DynamoDB Streams for analytics (vs. polling)
- Implement caching layer

---

## Testing Checklist

- [ ] Create user with all required attributes
- [ ] Create user with minimal attributes
- [ ] Update profile attributes
- [ ] Update preferences
- [ ] Update settings
- [ ] Create statistics for multiple leagues
- [ ] Query user profile by ID
- [ ] Query user preferences
- [ ] Query user settings
- [ ] Query user statistics by league
- [ ] Query all user statistics
- [ ] Validate email format
- [ ] Validate timezone format
- [ ] Validate country code format
- [ ] Test concurrent updates
- [ ] Test batch operations
- [ ] Test TTL for deleted accounts
- [ ] Test GSI1 queries
- [ ] Test pagination
- [ ] Load test with 1M+ users

---

## References

- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Single-Table Design](https://www.alexdebrie.com/posts/dynamodb-single-table/)
- [RFC 5322 - Email Format](https://tools.ietf.org/html/rfc5322)
- [ISO 8601 - Date/Time Format](https://en.wikipedia.org/wiki/ISO_8601)
- [IANA Timezone Database](https://www.iana.org/time-zones)
- [ISO 639-1 Language Codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
- [ISO 3166-1 Country Codes](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)

