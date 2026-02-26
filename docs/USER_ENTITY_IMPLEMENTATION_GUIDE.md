# USER Entity Implementation Guide

## Overview

This guide provides practical implementation details for integrating the USER entity specification into the Multi-Player platform. It includes code examples, best practices, and integration patterns.

## Table of Contents

1. [Model Usage](#model-usage)
2. [Repository Usage](#repository-usage)
3. [Lambda Function Integration](#lambda-function-integration)
4. [API Endpoints](#api-endpoints)
5. [Validation & Error Handling](#validation--error-handling)
6. [Testing](#testing)
7. [Migration Guide](#migration-guide)

---

## Model Usage

### Importing Models

```python
from models.user import (
    UserProfile,
    UserPreferences,
    UserSettings,
    UserStatistics,
    AccountStatus,
    GameType,
    ProfileVisibility
)
```

### Creating a User Profile

```python
from uuid import uuid4
from datetime import datetime
from models.user import UserProfile, AccountStatus

# Create a new user profile
user_id = str(uuid4())
profile = UserProfile(
    pk=f'USER#{user_id}',
    sk='PROFILE',
    entity_type='USER',
    user_id=user_id,
    email='john.doe@example.com',
    email_verified=True,
    name='John Doe',
    avatar_url='https://cdn.example.com/avatars/user123.jpg',
    bio='Fantasy football enthusiast',
    country='US',
    timezone='America/New_York',
    preferred_language='en',
    account_status=AccountStatus.ACTIVE,
    cognito_sub=user_id,
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)

# Convert to DynamoDB item
item = profile.to_dynamodb_item()
```

### Creating User Preferences

```python
from models.user import UserPreferences, GameType, ProfileVisibility

preferences = UserPreferences(
    pk=f'USER#{user_id}',
    sk='PREFERENCES',
    entity_type='USER_PREFERENCES',
    email_notifications_enabled=True,
    push_notifications_enabled=True,
    profile_visibility=ProfileVisibility.PUBLIC,
    preferred_game_type=GameType.POINTS_BASED,
    theme_preference='DARK',
    notification_frequency='DAILY'
)
```

### Creating User Settings

```python
from models.user import UserSettings, TwoFactorMethod

settings = UserSettings(
    pk=f'USER#{user_id}',
    sk='SETTINGS',
    entity_type='USER_SETTINGS',
    two_factor_enabled=True,
    two_factor_method=TwoFactorMethod.TOTP,
    session_timeout_minutes=30,
    api_keys_enabled=True,
    data_export_enabled=True
)
```

### Creating User Statistics

```python
from models.user import UserStatistics, GameType

# Points-based game statistics
stats = UserStatistics(
    pk=f'USER#{user_id}',
    sk=f'STATISTICS#{league_id}',
    gsi1_pk=f'USER#{user_id}',
    gsi1_sk=f'STAT#{league_id}',
    entity_type='USER_STATISTICS',
    user_id=user_id,
    league_id=league_id,
    game_type=GameType.POINTS_BASED,
    total_points=1250,
    current_rank=3,
    previous_rank=5,
    games_played=15,
    highest_score=150,
    lowest_score=45,
    total_predictions=150,
    correct_predictions=95
)

# Pydantic automatically calculates:
# - rank_change = 2 (5 - 3)
# - average_points_per_game = 83.33 (1250 / 15)
# - prediction_accuracy = 63.33 (95 / 150 * 100)
```

---

## Repository Usage

### Importing Repository

```python
from repository.user import UserRepository
from repository.table import DynamoDBTable

# Initialize repository
table = DynamoDBTable()
user_repo = UserRepository(table)
```

### Profile Operations

```python
# Get user profile
profile = user_repo.get_profile(user_id)

# Create user profile
user_repo.create_profile(profile)

# Update user profile
updates = {
    'bio': 'Updated bio',
    'avatar_url': 'https://new-avatar-url.jpg'
}
updated_profile = user_repo.update_profile(user_id, updates)
```

### Preferences Operations

```python
# Get user preferences
preferences = user_repo.get_preferences(user_id)

# Create user preferences
user_repo.create_preferences(user_id, preferences)

# Update user preferences
updates = {
    'theme_preference': 'LIGHT',
    'notification_frequency': 'WEEKLY'
}
updated_prefs = user_repo.update_preferences(user_id, updates)
```

### Settings Operations

```python
# Get user settings
settings = user_repo.get_settings(user_id)

# Create user settings
user_repo.create_settings(user_id, settings)

# Update user settings
updates = {
    'two_factor_enabled': True,
    'two_factor_method': 'TOTP'
}
updated_settings = user_repo.update_settings(user_id, updates)
```

### Statistics Operations

```python
# Get statistics for specific league
stats = user_repo.get_statistics(user_id, league_id)

# Get all statistics for user
all_stats = user_repo.get_all_statistics(user_id)

# Create statistics
user_repo.create_statistics(statistics)

# Update statistics
updates = {
    'total_points': 1300,
    'current_rank': 2,
    'games_played': 16
}
updated_stats = user_repo.update_statistics(user_id, league_id, updates)
```

### Batch Operations

```python
# Get all user data at once
user_data = user_repo.get_user_data(user_id)
# Returns: {
#     'profile': {...},
#     'preferences': {...},
#     'settings': {...},
#     'statistics': [...]
# }

# Create complete user profile
user_repo.create_user_complete(profile, preferences, settings)
```

### Utility Operations

```python
# Update last login
user_repo.update_last_login(user_id)

# Suspend user
user_repo.suspend_user(user_id)

# Reactivate user
user_repo.reactivate_user(user_id)

# Delete user (soft delete)
user_repo.delete_user(user_id)
```

---

## Lambda Function Integration

### Example: Create User Profile Function

```python
"""Create user profile Lambda function."""
import json
import os
import uuid
from datetime import datetime
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from pydantic import ValidationError

from models.user import UserProfile, UserPreferences, UserSettings, AccountStatus
from repository.user import UserRepository
from utils.responses import success_response, error_response

logger = Logger()
tracer = Tracer()
metrics = Metrics()

user_repo = UserRepository()


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Create user profile after Cognito signup.
    
    Expected body:
    {
        "email": "user@example.com",
        "name": "John Doe",
        "country": "US",
        "timezone": "America/New_York"
    }
    """
    try:
        # Get user ID from Cognito authorizer
        user_id = event['requestContext']['authorizer']['claims']['sub']
        email = event['requestContext']['authorizer']['claims'].get('email')
        
        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        country = body.get('country')
        timezone = body.get('timezone')
        
        if not name:
            return error_response(400, 'Name is required')
        
        # Create profile
        profile = UserProfile(
            pk=f'USER#{user_id}',
            sk='PROFILE',
            entity_type='USER',
            user_id=user_id,
            email=email,
            email_verified=True,
            name=name,
            country=country,
            timezone=timezone,
            account_status=AccountStatus.ACTIVE,
            cognito_sub=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Create preferences with defaults
        preferences = UserPreferences(
            pk=f'USER#{user_id}',
            sk='PREFERENCES',
            entity_type='USER_PREFERENCES',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Create settings with defaults
        settings = UserSettings(
            pk=f'USER#{user_id}',
            sk='SETTINGS',
            entity_type='USER_SETTINGS',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to DynamoDB
        user_repo.create_user_complete(profile, preferences, settings)
        
        logger.info(f"User profile created: {user_id}")
        metrics.add_metric(name="UserProfileCreated", unit="Count", value=1)
        
        return success_response(201, {
            'message': 'User profile created successfully',
            'user_id': user_id,
            'email': email,
            'name': name
        })
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return error_response(400, f'Validation error: {str(e)}')
    
    except Exception as e:
        logger.exception(f"Error creating user profile: {e}")
        return error_response(500, 'Internal server error')
```

### Example: Update User Preferences Function

```python
"""Update user preferences Lambda function."""
import json
import os
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from pydantic import ValidationError

from models.user import UserPreferences
from repository.user import UserRepository
from utils.responses import success_response, error_response

logger = Logger()
tracer = Tracer()
metrics = Metrics()

user_repo = UserRepository()


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Update user preferences.
    
    Expected body:
    {
        "theme_preference": "DARK",
        "notification_frequency": "WEEKLY",
        "email_notifications_enabled": false
    }
    """
    try:
        user_id = event['requestContext']['authorizer']['claims']['sub']
        body = json.loads(event.get('body', '{}'))
        
        # Validate preferences
        preferences = UserPreferences(**body)
        
        # Update preferences
        updates = preferences.dict(exclude_none=True)
        updated = user_repo.update_preferences(user_id, updates)
        
        logger.info(f"User preferences updated: {user_id}")
        metrics.add_metric(name="PreferencesUpdated", unit="Count", value=1)
        
        return success_response(200, {
            'message': 'Preferences updated successfully',
            'preferences': updated
        })
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return error_response(400, f'Validation error: {str(e)}')
    
    except Exception as e:
        logger.exception(f"Error updating preferences: {e}")
        return error_response(500, 'Internal server error')
```

### Example: Get User Statistics Function

```python
"""Get user statistics Lambda function."""
import json
import os
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths

from repository.user import UserRepository
from utils.responses import success_response, error_response

logger = Logger()
tracer = Tracer()
metrics = Metrics()

user_repo = UserRepository()


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Get user statistics for a league."""
    try:
        user_id = event['requestContext']['authorizer']['claims']['sub']
        league_id = event['pathParameters']['leagueId']
        
        # Get statistics
        stats = user_repo.get_statistics(user_id, league_id)
        
        if not stats:
            return error_response(404, 'Statistics not found')
        
        logger.info(f"Retrieved statistics for user {user_id} in league {league_id}")
        metrics.add_metric(name="StatisticsRetrieved", unit="Count", value=1)
        
        return success_response(200, {
            'statistics': stats
        })
    
    except Exception as e:
        logger.exception(f"Error getting statistics: {e}")
        return error_response(500, 'Internal server error')
```

---

## API Endpoints

### Create User Profile

**POST** `/api/users/profile`

**Request:**
```json
{
  "name": "John Doe",
  "country": "US",
  "timezone": "America/New_York",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "Fantasy football enthusiast"
}
```

**Response (201):**
```json
{
  "message": "User profile created successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "name": "John Doe"
}
```

### Get User Profile

**GET** `/api/users/profile`

**Response (200):**
```json
{
  "profile": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@example.com",
    "name": "John Doe",
    "avatar_url": "https://example.com/avatar.jpg",
    "bio": "Fantasy football enthusiast",
    "country": "US",
    "timezone": "America/New_York",
    "account_status": "ACTIVE",
    "created_at": "2024-01-15T10:30:45.123Z",
    "updated_at": "2024-01-20T14:22:10.456Z"
  }
}
```

### Update User Profile

**PUT** `/api/users/profile`

**Request:**
```json
{
  "bio": "Updated bio",
  "avatar_url": "https://new-avatar.jpg"
}
```

**Response (200):**
```json
{
  "message": "Profile updated successfully",
  "profile": { ... }
}
```

### Get User Preferences

**GET** `/api/users/preferences`

**Response (200):**
```json
{
  "preferences": {
    "email_notifications_enabled": true,
    "push_notifications_enabled": true,
    "theme_preference": "DARK",
    "notification_frequency": "DAILY",
    "preferred_game_type": "POINTS_BASED"
  }
}
```

### Update User Preferences

**PUT** `/api/users/preferences`

**Request:**
```json
{
  "theme_preference": "LIGHT",
  "notification_frequency": "WEEKLY"
}
```

**Response (200):**
```json
{
  "message": "Preferences updated successfully",
  "preferences": { ... }
}
```

### Get User Statistics

**GET** `/api/users/statistics/{leagueId}`

**Response (200):**
```json
{
  "statistics": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "league_id": "league-001",
    "game_type": "POINTS_BASED",
    "current_rank": 3,
    "total_points": 1250,
    "games_played": 15,
    "average_points_per_game": 83.33,
    "prediction_accuracy": 63.33,
    "joined_at": "2024-01-01T10:30:45.123Z",
    "updated_at": "2024-01-20T14:22:10.456Z"
  }
}
```

### Get All User Statistics

**GET** `/api/users/statistics`

**Response (200):**
```json
{
  "statistics": [
    { ... league 1 stats ... },
    { ... league 2 stats ... }
  ],
  "count": 2
}
```

---

## Validation & Error Handling

### Input Validation

```python
from pydantic import ValidationError
from models.user import UserProfile

try:
    profile = UserProfile(
        pk='USER#123',
        sk='PROFILE',
        entity_type='USER',
        user_id='123',
        email='invalid-email',  # Invalid email format
        name='John Doe'
    )
except ValidationError as e:
    print(e.json())
    # Output: [{"loc": ["email"], "msg": "invalid email format", ...}]
```

### Error Response Format

```python
from utils.responses import error_response

# 400 Bad Request
error_response(400, 'Invalid input')

# 404 Not Found
error_response(404, 'User not found')

# 409 Conflict
error_response(409, 'Email already exists')

# 500 Internal Server Error
error_response(500, 'Internal server error')
```

### Custom Validation

```python
from pydantic import validator
from models.user import UserProfile

class CustomUserProfile(UserProfile):
    @validator('email')
    def validate_email_domain(cls, v):
        """Ensure email is from allowed domains."""
        allowed_domains = ['example.com', 'company.com']
        domain = v.split('@')[1]
        if domain not in allowed_domains:
            raise ValueError(f'Email domain {domain} not allowed')
        return v
```

---

## Testing

### Unit Tests

```python
import pytest
from models.user import UserProfile, UserPreferences, UserStatistics, GameType
from datetime import datetime

def test_create_user_profile():
    """Test creating a user profile."""
    profile = UserProfile(
        pk='USER#123',
        sk='PROFILE',
        entity_type='USER',
        user_id='123',
        email='test@example.com',
        name='Test User',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    assert profile.user_id == '123'
    assert profile.email == 'test@example.com'
    assert profile.name == 'Test User'

def test_user_statistics_calculations():
    """Test automatic statistics calculations."""
    stats = UserStatistics(
        pk='USER#123',
        sk='STATISTICS#league-001',
        gsi1_pk='USER#123',
        gsi1_sk='STAT#league-001',
        entity_type='USER_STATISTICS',
        user_id='123',
        league_id='league-001',
        game_type=GameType.POINTS_BASED,
        total_points=1000,
        games_played=10,
        games_won=8,
        correct_predictions=80,
        total_predictions=100
    )
    
    assert stats.average_points_per_game == 100.0
    assert stats.win_percentage == 80.0
    assert stats.prediction_accuracy == 80.0

def test_invalid_email():
    """Test email validation."""
    with pytest.raises(ValidationError):
        UserProfile(
            pk='USER#123',
            sk='PROFILE',
            entity_type='USER',
            user_id='123',
            email='invalid-email',
            name='Test User'
        )
```

### Integration Tests

```python
import pytest
from repository.user import UserRepository
from models.user import UserProfile, UserPreferences, UserSettings
from datetime import datetime

@pytest.fixture
def user_repo():
    """Create user repository for testing."""
    return UserRepository()

def test_create_and_get_profile(user_repo):
    """Test creating and retrieving a user profile."""
    user_id = 'test-user-123'
    
    profile = UserProfile(
        pk=f'USER#{user_id}',
        sk='PROFILE',
        entity_type='USER',
        user_id=user_id,
        email='test@example.com',
        name='Test User',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Create
    user_repo.create_profile(profile)
    
    # Retrieve
    retrieved = user_repo.get_profile(user_id)
    
    assert retrieved is not None
    assert retrieved['user_id'] == user_id
    assert retrieved['email'] == 'test@example.com'

def test_update_preferences(user_repo):
    """Test updating user preferences."""
    user_id = 'test-user-123'
    
    # Create preferences
    prefs = UserPreferences(
        pk=f'USER#{user_id}',
        sk='PREFERENCES',
        entity_type='USER_PREFERENCES',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    user_repo.create_preferences(user_id, prefs)
    
    # Update
    updates = {'theme_preference': 'LIGHT'}
    updated = user_repo.update_preferences(user_id, updates)
    
    assert updated['theme_preference'] == 'LIGHT'
```

---

## Migration Guide

### From Existing System

If migrating from an existing user system:

1. **Export existing user data** to CSV/JSON
2. **Transform data** to match USER entity schema
3. **Validate data** against Pydantic models
4. **Batch import** to DynamoDB using batch_writer
5. **Verify data** with queries
6. **Run parallel** with old system for validation
7. **Cutover** to new system

### Example Migration Script

```python
import json
import uuid
from datetime import datetime
from models.user import UserProfile, UserPreferences, UserSettings
from repository.user import UserRepository

def migrate_users(input_file: str):
    """Migrate users from JSON file to DynamoDB."""
    user_repo = UserRepository()
    
    with open(input_file, 'r') as f:
        old_users = json.load(f)
    
    for old_user in old_users:
        user_id = str(uuid.uuid4())
        
        # Create profile
        profile = UserProfile(
            pk=f'USER#{user_id}',
            sk='PROFILE',
            entity_type='USER',
            user_id=user_id,
            email=old_user['email'],
            name=old_user['name'],
            country=old_user.get('country'),
            timezone=old_user.get('timezone'),
            created_at=datetime.fromisoformat(old_user['created_at']),
            updated_at=datetime.utcnow()
        )
        
        # Create preferences with defaults
        preferences = UserPreferences(
            pk=f'USER#{user_id}',
            sk='PREFERENCES',
            entity_type='USER_PREFERENCES',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Create settings with defaults
        settings = UserSettings(
            pk=f'USER#{user_id}',
            sk='SETTINGS',
            entity_type='USER_SETTINGS',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save
        user_repo.create_user_complete(profile, preferences, settings)
        print(f"Migrated user: {old_user['email']}")

if __name__ == '__main__':
    migrate_users('old_users.json')
```

---

## Best Practices

1. **Always validate input** using Pydantic models
2. **Use repository pattern** for data access
3. **Handle errors gracefully** with proper HTTP status codes
4. **Log important events** with correlation IDs
5. **Cache frequently accessed data** (profile, preferences)
6. **Use batch operations** for multiple items
7. **Implement soft deletes** for user data
8. **Monitor statistics updates** for performance
9. **Validate email uniqueness** at application level
10. **Use TTL** for temporary data (deleted accounts)

---

## References

- [USER Entity Specification](./USER_ENTITY_SPECIFICATION.md)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [AWS Lambda Powertools](https://docs.powertools.aws.dev/lambda/python/)
