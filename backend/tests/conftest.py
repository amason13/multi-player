"""Pytest configuration and shared fixtures for multi-player tests."""
import os
import sys
import json
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch

import pytest
import boto3
from moto import mock_aws
from pydantic import ValidationError

# Add src to path for imports - use common layer as package root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/layers/common'))

# Add src directory to path for function imports
src_path = os.path.join(os.path.dirname(__file__), '../src')
sys.path.insert(0, src_path)

# Add functions directory to path
functions_path = os.path.join(os.path.dirname(__file__), '../src/functions')
sys.path.insert(0, functions_path)

from python.models.user import (
    UserProfile, UserPreferences, UserSettings, UserStatistics,
    AccountStatus, ProfileVisibility, ThemePreference, NotificationFrequency, GameType
)
from python.repository import DynamoDBTable, UserRepository
from python.utils.exceptions import ValidationError as AppValidationError
from python.utils.responses import success_response, error_response


# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ['TABLE_NAME'] = 'test-table'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'


# ============================================================================
# DYNAMODB FIXTURES
# ============================================================================

@pytest.fixture
def dynamodb_table():
    """Create a mock DynamoDB table for testing."""
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create test table
        table = dynamodb.create_table(
            TableName='test-table',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        yield table


@pytest.fixture
def dynamodb_table_wrapper(dynamodb_table):
    """Create a DynamoDBTable wrapper for testing."""
    with patch.dict(os.environ, {'TABLE_NAME': 'test-table'}):
        with mock_aws():
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.create_table(
                TableName='test-table',
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'GSI1',
                        'KeySchema': [
                            {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                            {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            wrapper = DynamoDBTable('test-table')
            wrapper.table = table
            yield wrapper


# ============================================================================
# USER MODEL FIXTURES
# ============================================================================

@pytest.fixture
def user_id():
    """Generate a test user ID."""
    return str(uuid4())


@pytest.fixture
def league_id():
    """Generate a test league ID."""
    return str(uuid4())


@pytest.fixture
def valid_user_profile(user_id):
    """Create a valid UserProfile instance."""
    return UserProfile(
        pk=f'USER#{user_id}',
        sk='PROFILE',
        user_id=user_id,
        email='test@example.com',
        name='Test User',
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        cognito_sub='cognito-sub-123'
    )


@pytest.fixture
def valid_user_preferences(user_id):
    """Create a valid UserPreferences instance."""
    return UserPreferences(
        pk=f'USER#{user_id}',
        sk='PREFERENCES',
        email_notifications_enabled=True,
        push_notifications_enabled=True,
        profile_visibility=ProfileVisibility.PUBLIC,
        theme_preference=ThemePreference.AUTO,
        notification_frequency=NotificationFrequency.DAILY,
        preferred_game_type=GameType.BOTH
    )


@pytest.fixture
def valid_user_settings(user_id):
    """Create a valid UserSettings instance."""
    return UserSettings(
        pk=f'USER#{user_id}',
        sk='SETTINGS',
        two_factor_enabled=False,
        session_timeout_minutes=30,
        data_export_enabled=True
    )


@pytest.fixture
def valid_user_statistics(user_id, league_id):
    """Create a valid UserStatistics instance."""
    return UserStatistics(
        pk=f'USER#{user_id}',
        sk=f'STATISTICS#{league_id}',
        user_id=user_id,
        league_id=league_id,
        game_type=GameType.POINTS_BASED,
        total_points=150,
        current_rank=5,
        previous_rank=8,
        games_played=10,
        games_won=7,
        games_lost=3,
        total_predictions=20,
        correct_predictions=15
    )


# ============================================================================
# COGNITO FIXTURES
# ============================================================================

@pytest.fixture
def cognito_claims(user_id):
    """Create mock Cognito claims."""
    return {
        'sub': user_id,
        'email': 'test@example.com',
        'email_verified': 'true',
        'name': 'Test User',
        'cognito:username': 'testuser'
    }


@pytest.fixture
def lambda_event_with_auth(cognito_claims):
    """Create a Lambda event with Cognito authorization."""
    return {
        'requestContext': {
            'authorizer': {
                'claims': cognito_claims
            }
        },
        'headers': {
            'Content-Type': 'application/json'
        }
    }


@pytest.fixture
def lambda_context():
    """Create a mock Lambda context."""
    context = Mock()
    context.function_name = 'test-function'
    context.function_version = '$LATEST'
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test-function'
    context.memory_limit_in_mb = 512
    context.aws_request_id = 'test-request-id'
    context.log_group_name = '/aws/lambda/test-function'
    context.log_stream_name = 'test-stream'
    context.identity = Mock()
    context.get_remaining_time_in_millis = Mock(return_value=30000)
    return context


# ============================================================================
# RESPONSE FIXTURES
# ============================================================================

@pytest.fixture
def success_response_200():
    """Create a successful 200 response."""
    return success_response({'message': 'Success'}, status_code=200)


@pytest.fixture
def success_response_201():
    """Create a successful 201 response."""
    return success_response({'message': 'Created'}, status_code=201)


@pytest.fixture
def error_response_400():
    """Create a 400 error response."""
    return error_response('Bad Request', status_code=400, error_code='VALIDATION_ERROR')


@pytest.fixture
def error_response_401():
    """Create a 401 error response."""
    return error_response('Unauthorized', status_code=401, error_code='UNAUTHORIZED')


@pytest.fixture
def error_response_404():
    """Create a 404 error response."""
    return error_response('Not Found', status_code=404, error_code='NOT_FOUND')


@pytest.fixture
def error_response_500():
    """Create a 500 error response."""
    return error_response('Internal Server Error', status_code=500, error_code='INTERNAL_ERROR')


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_dynamodb_client():
    """Create a mock DynamoDB client."""
    return Mock(spec=boto3.client('dynamodb'))


@pytest.fixture
def mock_cognito_client():
    """Create a mock Cognito client."""
    return Mock(spec=boto3.client('cognito-idp'))


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return Mock()


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def sample_dynamodb_item(user_id):
    """Create a sample DynamoDB item."""
    return {
        'PK': f'USER#{user_id}',
        'SK': 'PROFILE',
        'user_id': user_id,
        'email': 'test@example.com',
        'name': 'Test User',
        'email_verified': True,
        'account_status': 'ACTIVE',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'entity_type': 'USER'
    }


@pytest.fixture
def sample_league_item(league_id, user_id):
    """Create a sample league DynamoDB item."""
    return {
        'PK': f'LEAGUE#{league_id}',
        'SK': 'METADATA',
        'GSI1PK': f'USER#{user_id}',
        'GSI1SK': f'LEAGUE#{league_id}',
        'league_id': league_id,
        'name': 'Test League',
        'description': 'A test league',
        'sport': 'football',
        'owner_id': user_id,
        'member_count': 1,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'entity_type': 'LEAGUE'
    }


@pytest.fixture
def sample_league_member_item(league_id, user_id):
    """Create a sample league member DynamoDB item."""
    return {
        'PK': f'LEAGUE#{league_id}',
        'SK': f'MEMBER#{user_id}',
        'user_id': user_id,
        'role': 'member',
        'joined_at': datetime.utcnow().isoformat(),
        'entity_type': 'LEAGUE_MEMBER'
    }
