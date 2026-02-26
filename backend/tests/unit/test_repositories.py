"""Unit tests for repository classes and DynamoDB operations."""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, call
from moto import mock_dynamodb
import boto3

from repository.table import DynamoDBTable
from repository.user import UserRepository
from models.user import (
    UserProfile, UserPreferences, UserSettings, UserStatistics,
    AccountStatus, GameType
)


class TestDynamoDBTable:
    """Test cases for DynamoDBTable wrapper."""
    
    @mock_dynamodb
    def test_dynamodb_table_initialization(self):
        """Test DynamoDBTable initialization."""
        with patch.dict('os.environ', {'TABLE_NAME': 'test-table'}):
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            dynamodb.create_table(
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
            
            table = DynamoDBTable('test-table')
            assert table.table_name == 'test-table'
            assert table.table is not None
    
    @mock_dynamodb
    def test_dynamodb_table_missing_env_var(self):
        """Test DynamoDBTable raises error when TABLE_NAME not set."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match='TABLE_NAME environment variable not set'):
                DynamoDBTable()
    
    @mock_dynamodb
    def test_get_item_success(self, dynamodb_table_wrapper):
        """Test getting an item from DynamoDB."""
        # Put an item first
        item = {
            'PK': 'USER#123',
            'SK': 'PROFILE',
            'user_id': '123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        dynamodb_table_wrapper.put_item(item)
        
        # Get the item
        result = dynamodb_table_wrapper.get_item('USER#123', 'PROFILE')
        
        assert result is not None
        assert result['PK'] == 'USER#123'
        assert result['SK'] == 'PROFILE'
        assert result['email'] == 'test@example.com'
    
    @mock_dynamodb
    def test_get_item_not_found(self, dynamodb_table_wrapper):
        """Test getting a non-existent item returns None."""
        result = dynamodb_table_wrapper.get_item('USER#999', 'PROFILE')
        assert result is None
    
    @mock_dynamodb
    def test_put_item_success(self, dynamodb_table_wrapper):
        """Test putting an item into DynamoDB."""
        item = {
            'PK': 'USER#123',
            'SK': 'PROFILE',
            'user_id': '123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        dynamodb_table_wrapper.put_item(item)
        
        # Verify item was stored
        result = dynamodb_table_wrapper.get_item('USER#123', 'PROFILE')
        assert result is not None
        assert result['email'] == 'test@example.com'
    
    @mock_dynamodb
    def test_update_item_success(self, dynamodb_table_wrapper):
        """Test updating an item in DynamoDB."""
        # Put initial item
        item = {
            'PK': 'USER#123',
            'SK': 'PROFILE',
            'user_id': '123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        dynamodb_table_wrapper.put_item(item)
        
        # Update the item
        updates = {
            'name': 'Updated User',
            'email': 'updated@example.com'
        }
        result = dynamodb_table_wrapper.update_item('USER#123', 'PROFILE', updates)
        
        assert result['name'] == 'Updated User'
        assert result['email'] == 'updated@example.com'
    
    @mock_dynamodb
    def test_delete_item_success(self, dynamodb_table_wrapper):
        """Test deleting an item from DynamoDB."""
        # Put an item first
        item = {
            'PK': 'USER#123',
            'SK': 'PROFILE',
            'user_id': '123',
            'email': 'test@example.com'
        }
        dynamodb_table_wrapper.put_item(item)
        
        # Delete the item
        dynamodb_table_wrapper.delete_item('USER#123', 'PROFILE')
        
        # Verify item was deleted
        result = dynamodb_table_wrapper.get_item('USER#123', 'PROFILE')
        assert result is None
    
    @mock_dynamodb
    def test_query_by_pk_success(self, dynamodb_table_wrapper):
        """Test querying items by partition key."""
        # Put multiple items
        items = [
            {'PK': 'USER#123', 'SK': 'PROFILE', 'user_id': '123'},
            {'PK': 'USER#123', 'SK': 'PREFERENCES', 'user_id': '123'},
            {'PK': 'USER#123', 'SK': 'SETTINGS', 'user_id': '123'}
        ]
        for item in items:
            dynamodb_table_wrapper.put_item(item)
        
        # Query by PK
        results = dynamodb_table_wrapper.query('USER#123')
        
        assert len(results) == 3
        assert all(item['PK'] == 'USER#123' for item in results)
    
    @mock_dynamodb
    def test_query_by_pk_with_sk_prefix(self, dynamodb_table_wrapper):
        """Test querying items by partition key with sort key prefix."""
        # Put multiple items
        items = [
            {'PK': 'USER#123', 'SK': 'PROFILE', 'user_id': '123'},
            {'PK': 'USER#123', 'SK': 'PREFERENCES', 'user_id': '123'},
            {'PK': 'USER#123', 'SK': 'STATISTICS#league1', 'user_id': '123'},
            {'PK': 'USER#123', 'SK': 'STATISTICS#league2', 'user_id': '123'}
        ]
        for item in items:
            dynamodb_table_wrapper.put_item(item)
        
        # Query with SK prefix
        results = dynamodb_table_wrapper.query('USER#123', 'STATISTICS#')
        
        assert len(results) == 2
        assert all(item['SK'].startswith('STATISTICS#') for item in results)
    
    @mock_dynamodb
    def test_query_empty_result(self, dynamodb_table_wrapper):
        """Test querying with no results."""
        results = dynamodb_table_wrapper.query('USER#999')
        assert results == []


class TestUserRepository:
    """Test cases for UserRepository."""
    
    @mock_dynamodb
    def test_user_repository_initialization(self, dynamodb_table_wrapper):
        """Test UserRepository initialization."""
        repo = UserRepository(dynamodb_table_wrapper)
        assert repo.table is not None
    
    @mock_dynamodb
    def test_get_profile_success(self, dynamodb_table_wrapper, user_id, valid_user_profile):
        """Test getting a user profile."""
        # Create profile
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_profile(valid_user_profile)
        
        # Get profile
        result = repo.get_profile(user_id)
        
        assert result is not None
        assert result['user_id'] == user_id
        assert result['email'] == 'test@example.com'
    
    @mock_dynamodb
    def test_get_profile_not_found(self, dynamodb_table_wrapper):
        """Test getting a non-existent profile."""
        repo = UserRepository(dynamodb_table_wrapper)
        result = repo.get_profile('non-existent-id')
        assert result is None
    
    @mock_dynamodb
    def test_create_profile_success(self, dynamodb_table_wrapper, user_id, valid_user_profile):
        """Test creating a user profile."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_profile(valid_user_profile)
        
        # Verify profile was created
        result = repo.get_profile(user_id)
        assert result is not None
        assert result['user_id'] == user_id
    
    @mock_dynamodb
    def test_update_profile_success(self, dynamodb_table_wrapper, user_id, valid_user_profile):
        """Test updating a user profile."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_profile(valid_user_profile)
        
        # Update profile
        updates = {
            'name': 'Updated Name',
            'bio': 'Updated bio'
        }
        result = repo.update_profile(user_id, updates)
        
        assert result['name'] == 'Updated Name'
        assert result['bio'] == 'Updated bio'
    
    @mock_dynamodb
    def test_get_preferences_success(self, dynamodb_table_wrapper, user_id, valid_user_preferences):
        """Test getting user preferences."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_preferences(user_id, valid_user_preferences)
        
        result = repo.get_preferences(user_id)
        
        assert result is not None
        assert result['email_notifications_enabled'] is True
    
    @mock_dynamodb
    def test_create_preferences_success(self, dynamodb_table_wrapper, user_id, valid_user_preferences):
        """Test creating user preferences."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_preferences(user_id, valid_user_preferences)
        
        result = repo.get_preferences(user_id)
        assert result is not None
    
    @mock_dynamodb
    def test_update_preferences_success(self, dynamodb_table_wrapper, user_id, valid_user_preferences):
        """Test updating user preferences."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_preferences(user_id, valid_user_preferences)
        
        updates = {
            'email_notifications_enabled': False,
            'theme_preference': 'DARK'
        }
        result = repo.update_preferences(user_id, updates)
        
        assert result['email_notifications_enabled'] is False
        assert result['theme_preference'] == 'DARK'
    
    @mock_dynamodb
    def test_get_settings_success(self, dynamodb_table_wrapper, user_id, valid_user_settings):
        """Test getting user settings."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_settings(user_id, valid_user_settings)
        
        result = repo.get_settings(user_id)
        
        assert result is not None
        assert result['session_timeout_minutes'] == 30
    
    @mock_dynamodb
    def test_create_settings_success(self, dynamodb_table_wrapper, user_id, valid_user_settings):
        """Test creating user settings."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_settings(user_id, valid_user_settings)
        
        result = repo.get_settings(user_id)
        assert result is not None
    
    @mock_dynamodb
    def test_update_settings_success(self, dynamodb_table_wrapper, user_id, valid_user_settings):
        """Test updating user settings."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_settings(user_id, valid_user_settings)
        
        updates = {
            'two_factor_enabled': True,
            'session_timeout_minutes': 60
        }
        result = repo.update_settings(user_id, updates)
        
        assert result['two_factor_enabled'] is True
        assert result['session_timeout_minutes'] == 60
    
    @mock_dynamodb
    def test_get_statistics_success(self, dynamodb_table_wrapper, user_id, league_id, valid_user_statistics):
        """Test getting user statistics."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_statistics(valid_user_statistics)
        
        result = repo.get_statistics(user_id, league_id)
        
        assert result is not None
        assert result['user_id'] == user_id
        assert result['league_id'] == league_id
    
    @mock_dynamodb
    def test_create_statistics_success(self, dynamodb_table_wrapper, user_id, league_id, valid_user_statistics):
        """Test creating user statistics."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_statistics(valid_user_statistics)
        
        result = repo.get_statistics(user_id, league_id)
        assert result is not None
    
    @mock_dynamodb
    def test_update_statistics_success(self, dynamodb_table_wrapper, user_id, league_id, valid_user_statistics):
        """Test updating user statistics."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_statistics(valid_user_statistics)
        
        updates = {
            'total_points': 200,
            'games_played': 15
        }
        result = repo.update_statistics(user_id, league_id, updates)
        
        assert result['total_points'] == 200
        assert result['games_played'] == 15
    
    @mock_dynamodb
    def test_get_all_statistics_success(self, dynamodb_table_wrapper, user_id):
        """Test getting all statistics for a user."""
        repo = UserRepository(dynamodb_table_wrapper)
        
        # Create statistics for multiple leagues
        league_ids = ['league1', 'league2', 'league3']
        for league_id in league_ids:
            stats = UserStatistics(
                pk=f'USER#{user_id}',
                sk=f'STATISTICS#{league_id}',
                user_id=user_id,
                league_id=league_id,
                game_type=GameType.POINTS_BASED,
                entity_type='USER_STATISTICS'
            )
            repo.create_statistics(stats)
        
        results = repo.get_all_statistics(user_id)
        
        assert len(results) == 3
        assert all(item['user_id'] == user_id for item in results)
    
    @mock_dynamodb
    def test_get_user_data_complete(self, dynamodb_table_wrapper, user_id, league_id, 
                                    valid_user_profile, valid_user_preferences, 
                                    valid_user_settings, valid_user_statistics):
        """Test getting all user data."""
        repo = UserRepository(dynamodb_table_wrapper)
        
        # Create all user data
        repo.create_profile(valid_user_profile)
        repo.create_preferences(user_id, valid_user_preferences)
        repo.create_settings(user_id, valid_user_settings)
        repo.create_statistics(valid_user_statistics)
        
        # Get all user data
        user_data = repo.get_user_data(user_id)
        
        assert user_data['profile'] is not None
        assert user_data['preferences'] is not None
        assert user_data['settings'] is not None
        assert len(user_data['statistics']) == 1
    
    @mock_dynamodb
    def test_create_user_complete_success(self, dynamodb_table_wrapper, user_id, 
                                         valid_user_profile, valid_user_preferences, 
                                         valid_user_settings):
        """Test creating complete user profile with all data."""
        repo = UserRepository(dynamodb_table_wrapper)
        
        repo.create_user_complete(valid_user_profile, valid_user_preferences, valid_user_settings)
        
        # Verify all data was created
        profile = repo.get_profile(user_id)
        preferences = repo.get_preferences(user_id)
        settings = repo.get_settings(user_id)
        
        assert profile is not None
        assert preferences is not None
        assert settings is not None
    
    @mock_dynamodb
    def test_delete_user_soft_delete(self, dynamodb_table_wrapper, user_id, valid_user_profile):
        """Test soft deleting a user."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_profile(valid_user_profile)
        
        # Delete user
        repo.delete_user(user_id)
        
        # Verify user is marked as deleted
        result = repo.get_profile(user_id)
        assert result['account_status'] == 'DELETED'
    
    @mock_dynamodb
    def test_suspend_user_success(self, dynamodb_table_wrapper, user_id, valid_user_profile):
        """Test suspending a user."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_profile(valid_user_profile)
        
        # Suspend user
        repo.suspend_user(user_id)
        
        # Verify user is suspended
        result = repo.get_profile(user_id)
        assert result['account_status'] == 'SUSPENDED'
    
    @mock_dynamodb
    def test_reactivate_user_success(self, dynamodb_table_wrapper, user_id, valid_user_profile):
        """Test reactivating a user."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_profile(valid_user_profile)
        
        # Suspend then reactivate
        repo.suspend_user(user_id)
        repo.reactivate_user(user_id)
        
        # Verify user is active
        result = repo.get_profile(user_id)
        assert result['account_status'] == 'ACTIVE'
    
    @mock_dynamodb
    def test_update_last_login_success(self, dynamodb_table_wrapper, user_id, valid_user_profile):
        """Test updating last login timestamp."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_profile(valid_user_profile)
        
        # Update last login
        repo.update_last_login(user_id)
        
        # Verify last login was updated
        result = repo.get_profile(user_id)
        assert result['last_login_at'] is not None
        assert result['login_count'] == 1
    
    @mock_dynamodb
    def test_update_last_login_increments_count(self, dynamodb_table_wrapper, user_id, valid_user_profile):
        """Test that update_last_login increments login count."""
        repo = UserRepository(dynamodb_table_wrapper)
        repo.create_profile(valid_user_profile)
        
        # Update last login multiple times
        repo.update_last_login(user_id)
        repo.update_last_login(user_id)
        repo.update_last_login(user_id)
        
        # Verify login count
        result = repo.get_profile(user_id)
        assert result['login_count'] == 3


class TestDynamoDBTableErrorHandling:
    """Test error handling in DynamoDBTable."""
    
    @mock_dynamodb
    def test_get_item_handles_exception(self, dynamodb_table_wrapper):
        """Test that get_item handles exceptions gracefully."""
        # Mock the table to raise an exception
        dynamodb_table_wrapper.table.get_item = Mock(side_effect=Exception('DynamoDB error'))
        
        with pytest.raises(Exception):
            dynamodb_table_wrapper.get_item('USER#123', 'PROFILE')
    
    @mock_dynamodb
    def test_put_item_handles_exception(self, dynamodb_table_wrapper):
        """Test that put_item handles exceptions gracefully."""
        dynamodb_table_wrapper.table.put_item = Mock(side_effect=Exception('DynamoDB error'))
        
        with pytest.raises(Exception):
            dynamodb_table_wrapper.put_item({'PK': 'TEST', 'SK': 'TEST'})
    
    @mock_dynamodb
    def test_update_item_handles_exception(self, dynamodb_table_wrapper):
        """Test that update_item handles exceptions gracefully."""
        dynamodb_table_wrapper.table.update_item = Mock(side_effect=Exception('DynamoDB error'))
        
        with pytest.raises(Exception):
            dynamodb_table_wrapper.update_item('USER#123', 'PROFILE', {'name': 'Test'})
    
    @mock_dynamodb
    def test_delete_item_handles_exception(self, dynamodb_table_wrapper):
        """Test that delete_item handles exceptions gracefully."""
        dynamodb_table_wrapper.table.delete_item = Mock(side_effect=Exception('DynamoDB error'))
        
        with pytest.raises(Exception):
            dynamodb_table_wrapper.delete_item('USER#123', 'PROFILE')
    
    @mock_dynamodb
    def test_query_handles_exception(self, dynamodb_table_wrapper):
        """Test that query handles exceptions gracefully."""
        dynamodb_table_wrapper.table.query = Mock(side_effect=Exception('DynamoDB error'))
        
        with pytest.raises(Exception):
            dynamodb_table_wrapper.query('USER#123')
