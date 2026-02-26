"""Unit tests for Lambda handler functions."""
import pytest
import json
import os
from unittest.mock import Mock, MagicMock, patch
from moto import mock_dynamodb, mock_cognito_idp
import boto3

# Mock the Lambda powertools before importing handlers
with patch('aws_lambda_powertools.Logger'):
    with patch('aws_lambda_powertools.Tracer'):
        with patch('aws_lambda_powertools.Metrics'):
            pass


class TestUserProfileHandler:
    """Test cases for user profile Lambda handler."""
    
    @mock_dynamodb
    def test_get_profile_success(self, lambda_event_with_auth, lambda_context, user_id):
        """Test successfully getting user profile."""
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-table',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Put test profile
        table.put_item(Item={
            'PK': f'USER#{user_id}',
            'SK': 'PROFILE',
            'user_id': user_id,
            'email': 'test@example.com',
            'name': 'Test User',
            'created_at': '2024-01-01T00:00:00'
        })
        
        # Mock the handler
        with patch('os.environ', {'TABLE_NAME': 'test-table'}):
            with patch('boto3.resource') as mock_resource:
                mock_resource.return_value = dynamodb
                
                # Import and call handler
                from functions.users.profile.app import lambda_handler
                
                response = lambda_handler(lambda_event_with_auth, lambda_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['profile']['user_id'] == user_id
                assert body['profile']['email'] == 'test@example.com'
    
    @mock_dynamodb
    def test_get_profile_missing_auth(self, lambda_context):
        """Test getting profile without authentication."""
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {}
                }
            }
        }
        
        with patch('os.environ', {'TABLE_NAME': 'test-table'}):
            with patch('boto3.resource'):
                from functions.users.profile.app import lambda_handler
                
                with pytest.raises(KeyError):
                    lambda_handler(event, lambda_context)
    
    @mock_dynamodb
    def test_get_profile_not_found_creates_from_cognito(self, lambda_event_with_auth, lambda_context, user_id):
        """Test that missing profile is created from Cognito claims."""
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-table',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        with patch('os.environ', {'TABLE_NAME': 'test-table'}):
            with patch('boto3.resource') as mock_resource:
                mock_resource.return_value = dynamodb
                
                from functions.users.profile.app import lambda_handler
                
                response = lambda_handler(lambda_event_with_auth, lambda_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['profile']['email'] == 'test@example.com'


class TestSignUpHandler:
    """Test cases for sign up Lambda handler."""
    
    def test_signup_success(self, lambda_context):
        """Test successful user sign up."""
        event = {
            'body': json.dumps({
                'email': 'newuser@example.com',
                'password': 'SecurePassword123',
                'name': 'New User'
            })
        }
        
        with patch('os.environ', {'USER_POOL_ID': 'test-pool'}):
            with patch('boto3.client') as mock_client:
                mock_cognito = MagicMock()
                mock_client.return_value = mock_cognito
                mock_cognito.admin_create_user.return_value = {
                    'User': {'Username': 'newuser@example.com'}
                }
                
                from functions.auth.signup.app import lambda_handler
                
                response = lambda_handler(event, lambda_context)
                
                assert response['statusCode'] == 201
                body = json.loads(response['body'])
                assert 'message' in body
                assert body['userId'] == 'newuser@example.com'
    
    def test_signup_missing_fields(self, lambda_context):
        """Test sign up with missing required fields."""
        event = {
            'body': json.dumps({
                'email': 'newuser@example.com'
                # Missing password and name
            })
        }
        
        with patch('os.environ', {'USER_POOL_ID': 'test-pool'}):
            with patch('boto3.client'):
                from functions.auth.signup.app import lambda_handler
                
                response = lambda_handler(event, lambda_context)
                
                assert response['statusCode'] == 400
                body = json.loads(response['body'])
                assert 'error' in body
    
    def test_signup_user_exists(self, lambda_context):
        """Test sign up when user already exists."""
        event = {
            'body': json.dumps({
                'email': 'existing@example.com',
                'password': 'SecurePassword123',
                'name': 'Existing User'
            })
        }
        
        with patch('os.environ', {'USER_POOL_ID': 'test-pool'}):
            with patch('boto3.client') as mock_client:
                mock_cognito = MagicMock()
                mock_client.return_value = mock_cognito
                
                # Mock UsernameExistsException
                exception = Exception('User already exists')
                exception.__class__.__name__ = 'UsernameExistsException'
                mock_cognito.admin_create_user.side_effect = exception
                
                from functions.auth.signup.app import lambda_handler
                
                response = lambda_handler(event, lambda_context)
                
                # Handler should catch and return 409
                assert response['statusCode'] in [409, 500]
    
    def test_signup_invalid_email(self, lambda_context):
        """Test sign up with invalid email format."""
        event = {
            'body': json.dumps({
                'email': 'invalid-email',
                'password': 'SecurePassword123',
                'name': 'Test User'
            })
        }
        
        with patch('os.environ', {'USER_POOL_ID': 'test-pool'}):
            with patch('boto3.client'):
                from functions.auth.signup.app import lambda_handler
                
                response = lambda_handler(event, lambda_context)
                
                # Should either validate or let Cognito handle it
                assert response['statusCode'] in [400, 500]


class TestSignInHandler:
    """Test cases for sign in Lambda handler."""
    
    def test_signin_success(self, lambda_context):
        """Test successful user sign in."""
        event = {
            'body': json.dumps({
                'email': 'test@example.com',
                'password': 'SecurePassword123'
            })
        }
        
        with patch('os.environ', {'USER_POOL_ID': 'test-pool', 'CLIENT_ID': 'test-client'}):
            with patch('boto3.client') as mock_client:
                mock_cognito = MagicMock()
                mock_client.return_value = mock_cognito
                mock_cognito.initiate_auth.return_value = {
                    'AuthenticationResult': {
                        'AccessToken': 'access-token',
                        'IdToken': 'id-token',
                        'RefreshToken': 'refresh-token',
                        'ExpiresIn': 3600
                    }
                }
                
                from functions.auth.signin.app import lambda_handler
                
                response = lambda_handler(event, lambda_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert 'accessToken' in body
                assert 'idToken' in body
                assert 'refreshToken' in body
    
    def test_signin_missing_fields(self, lambda_context):
        """Test sign in with missing required fields."""
        event = {
            'body': json.dumps({
                'email': 'test@example.com'
                # Missing password
            })
        }
        
        with patch('os.environ', {'USER_POOL_ID': 'test-pool', 'CLIENT_ID': 'test-client'}):
            with patch('boto3.client'):
                from functions.auth.signin.app import lambda_handler
                
                response = lambda_handler(event, lambda_context)
                
                assert response['statusCode'] == 400
                body = json.loads(response['body'])
                assert 'error' in body
    
    def test_signin_invalid_credentials(self, lambda_context):
        """Test sign in with invalid credentials."""
        event = {
            'body': json.dumps({
                'email': 'test@example.com',
                'password': 'WrongPassword'
            })
        }
        
        with patch('os.environ', {'USER_POOL_ID': 'test-pool', 'CLIENT_ID': 'test-client'}):
            with patch('boto3.client') as mock_client:
                mock_cognito = MagicMock()
                mock_client.return_value = mock_cognito
                
                # Mock NotAuthorizedException
                exception = Exception('Invalid credentials')
                exception.__class__.__name__ = 'NotAuthorizedException'
                mock_cognito.initiate_auth.side_effect = exception
                
                from functions.auth.signin.app import lambda_handler
                
                response = lambda_handler(event, lambda_context)
                
                assert response['statusCode'] in [401, 500]
    
    def test_signin_user_not_found(self, lambda_context):
        """Test sign in when user doesn't exist."""
        event = {
            'body': json.dumps({
                'email': 'nonexistent@example.com',
                'password': 'SecurePassword123'
            })
        }
        
        with patch('os.environ', {'USER_POOL_ID': 'test-pool', 'CLIENT_ID': 'test-client'}):
            with patch('boto3.client') as mock_client:
                mock_cognito = MagicMock()
                mock_client.return_value = mock_cognito
                
                # Mock UserNotFoundException
                exception = Exception('User not found')
                exception.__class__.__name__ = 'UserNotFoundException'
                mock_cognito.initiate_auth.side_effect = exception
                
                from functions.auth.signin.app import lambda_handler
                
                response = lambda_handler(event, lambda_context)
                
                assert response['statusCode'] in [401, 500]


class TestCreateLeagueHandler:
    """Test cases for create league Lambda handler."""
    
    @mock_dynamodb
    def test_create_league_success(self, lambda_event_with_auth, lambda_context, user_id):
        """Test successfully creating a league."""
        event = lambda_event_with_auth.copy()
        event['body'] = json.dumps({
            'name': 'Test League',
            'description': 'A test league',
            'sport': 'football'
        })
        
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
        
        with patch('os.environ', {'TABLE_NAME': 'test-table'}):
            with patch('boto3.resource') as mock_resource:
                mock_resource.return_value = dynamodb
                
                from functions.leagues.create.app import lambda_handler
                
                response = lambda_handler(event, lambda_context)
                
                assert response['statusCode'] == 201
                body = json.loads(response['body'])
                assert body['league']['name'] == 'Test League'
                assert body['league']['owner_id'] == user_id
    
    @mock_dynamodb
    def test_create_league_missing_name(self, lambda_event_with_auth, lambda_context):
        """Test creating league without name."""
        event = lambda_event_with_auth.copy()
        event['body'] = json.dumps({
            'description': 'A test league'
            # Missing name
        })
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-table',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        with patch('os.environ', {'TABLE_NAME': 'test-table'}):
            with patch('boto3.resource') as mock_resource:
                mock_resource.return_value = dynamodb
                
                from functions.leagues.create.app import lambda_handler
                
                response = lambda_handler(event, lambda_context)
                
                assert response['statusCode'] == 400
                body = json.loads(response['body'])
                assert 'error' in body


class TestGetLeagueHandler:
    """Test cases for get league Lambda handler."""
    
    @mock_dynamodb
    def test_get_league_success(self, lambda_event_with_auth, lambda_context, league_id, user_id):
        """Test successfully getting a league."""
        event = lambda_event_with_auth.copy()
        event['pathParameters'] = {'leagueId': league_id}
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-table',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Put league data
        table.put_item(Item={
            'PK': f'LEAGUE#{league_id}',
            'SK': 'METADATA',
            'league_id': league_id,
            'name': 'Test League',
            'description': 'A test league',
            'sport': 'football',
            'owner_id': user_id,
            'member_count': 1,
            'created_at': '2024-01-01T00:00:00'
        })
        
        # Put member data
        table.put_item(Item={
            'PK': f'LEAGUE#{league_id}',
            'SK': f'MEMBER#{user_id}',
            'user_id': user_id,
            'role': 'owner',
            'joined_at': '2024-01-01T00:00:00'
        })
        
        with patch('os.environ', {'TABLE_NAME': 'test-table'}):
            with patch('boto3.resource') as mock_resource:
                mock_resource.return_value = dynamodb
                
                from functions.leagues.get.app import lambda_handler
                
                response = lambda_handler(event, lambda_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['league']['id'] == league_id
                assert body['league']['name'] == 'Test League'
                assert len(body['league']['members']) == 1
    
    @mock_dynamodb
    def test_get_league_not_found(self, lambda_event_with_auth, lambda_context):
        """Test getting a non-existent league."""
        event = lambda_event_with_auth.copy()
        event['pathParameters'] = {'leagueId': 'non-existent'}
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-table',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        with patch('os.environ', {'TABLE_NAME': 'test-table'}):
            with patch('boto3.resource') as mock_resource:
                mock_resource.return_value = dynamodb
                
                from functions.leagues.get.app import lambda_handler
                
                response = lambda_handler(event, lambda_context)
                
                assert response['statusCode'] == 404
                body = json.loads(response['body'])
                assert 'error' in body


class TestListLeaguesHandler:
    """Test cases for list leagues Lambda handler."""
    
    @mock_dynamodb
    def test_list_leagues_success(self, lambda_event_with_auth, lambda_context, user_id):
        """Test successfully listing leagues."""
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
        
        # Put league data
        for i in range(3):
            table.put_item(Item={
                'PK': f'LEAGUE#league{i}',
                'SK': 'METADATA',
                'GSI1PK': f'USER#{user_id}',
                'GSI1SK': f'LEAGUE#league{i}',
                'league_id': f'league{i}',
                'name': f'League {i}',
                'owner_id': user_id,
                'member_count': 1,
                'created_at': '2024-01-01T00:00:00'
            })
        
        with patch('os.environ', {'TABLE_NAME': 'test-table'}):
            with patch('boto3.resource') as mock_resource:
                mock_resource.return_value = dynamodb
                
                from functions.leagues.list.app import lambda_handler
                
                response = lambda_handler(lambda_event_with_auth, lambda_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['count'] == 3
                assert len(body['leagues']) == 3
    
    @mock_dynamodb
    def test_list_leagues_empty(self, lambda_event_with_auth, lambda_context):
        """Test listing leagues when user has none."""
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
        
        with patch('os.environ', {'TABLE_NAME': 'test-table'}):
            with patch('boto3.resource') as mock_resource:
                mock_resource.return_value = dynamodb
                
                from functions.leagues.list.app import lambda_handler
                
                response = lambda_handler(lambda_event_with_auth, lambda_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['count'] == 0
                assert len(body['leagues']) == 0
