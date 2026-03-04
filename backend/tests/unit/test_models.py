"""Unit tests for entity models and Pydantic validation."""
import pytest
from datetime import datetime
from pydantic import ValidationError

from python.models.base import BaseEntity
from python.models.user import (
    UserProfile, UserPreferences, UserSettings, UserStatistics,
    AccountStatus, ProfileVisibility, ThemePreference, NotificationFrequency, GameType,
    UserProfileResponse, UserStatisticsResponse
)


class TestBaseEntity:
    """Test cases for BaseEntity model."""
    
    def test_base_entity_creation(self):
        """Test creating a BaseEntity instance."""
        entity = BaseEntity(
            pk='TEST#123',
            sk='METADATA',
            entity_type='TEST'
        )
        assert entity.pk == 'TEST#123'
        assert entity.sk == 'METADATA'
        assert entity.entity_type == 'TEST'
        assert entity.created_at is not None
        assert entity.updated_at is not None
    
    def test_base_entity_with_gsi_keys(self):
        """Test BaseEntity with GSI keys."""
        entity = BaseEntity(
            pk='USER#123',
            sk='PROFILE',
            gsi1_pk='LEAGUE#456',
            gsi1_sk='MEMBER#123',
            entity_type='USER'
        )
        assert entity.gsi1_pk == 'LEAGUE#456'
        assert entity.gsi1_sk == 'MEMBER#123'
    
    def test_base_entity_with_ttl(self):
        """Test BaseEntity with TTL."""
        ttl_value = 1704067200
        entity = BaseEntity(
            pk='TEST#123',
            sk='METADATA',
            entity_type='TEST',
            ttl=ttl_value
        )
        assert entity.ttl == ttl_value
    
    def test_base_entity_to_dynamodb_item(self):
        """Test converting BaseEntity to DynamoDB item format."""
        entity = BaseEntity(
            pk='TEST#123',
            sk='METADATA',
            entity_type='TEST'
        )
        item = entity.to_dynamodb_item()
        
        assert item['pk'] == 'TEST#123'
        assert item['sk'] == 'METADATA'
        assert item['entity_type'] == 'TEST'
        assert isinstance(item['created_at'], str)
        assert isinstance(item['updated_at'], str)
    
    def test_base_entity_to_dynamodb_item_excludes_none(self):
        """Test that to_dynamodb_item excludes None values."""
        entity = BaseEntity(
            pk='TEST#123',
            sk='METADATA',
            entity_type='TEST',
            gsi1_pk=None,
            ttl=None
        )
        item = entity.to_dynamodb_item()
        
        assert 'gsi1_pk' not in item
        assert 'ttl' not in item
    
    def test_base_entity_missing_required_fields(self):
        """Test that BaseEntity requires pk, sk, and entity_type."""
        with pytest.raises(ValidationError) as exc_info:
            BaseEntity(pk='TEST#123', sk='METADATA')
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('entity_type',) for error in errors)
    
    def test_base_entity_datetime_serialization(self):
        """Test that datetime fields are properly serialized."""
        entity = BaseEntity(
            pk='TEST#123',
            sk='METADATA',
            entity_type='TEST'
        )
        item = entity.to_dynamodb_item()
        
        # Should be ISO format strings
        assert isinstance(item['created_at'], str)
        assert 'T' in item['created_at']
        assert isinstance(item['updated_at'], str)
        assert 'T' in item['updated_at']


class TestUserProfile:
    """Test cases for UserProfile model."""
    
    def test_user_profile_creation(self, user_id):
        """Test creating a UserProfile instance."""
        profile = UserProfile(
            pk=f'USER#{user_id}',
            sk='PROFILE',
            user_id=user_id,
            email='test@example.com',
            name='Test User',
            entity_type='USER'
        )
        assert profile.user_id == user_id
        assert profile.email == 'test@example.com'
        assert profile.name == 'Test User'
        assert profile.account_status == AccountStatus.ACTIVE
        assert profile.email_verified is False
    
    def test_user_profile_with_optional_fields(self, user_id):
        """Test UserProfile with optional fields."""
        profile = UserProfile(
            pk=f'USER#{user_id}',
            sk='PROFILE',
            user_id=user_id,
            email='test@example.com',
            name='Test User',
            entity_type='USER',
            avatar_url='https://example.com/avatar.jpg',
            bio='Test bio',
            phone_number='+1234567890',
            country='US',
            timezone='America/New_York',
            preferred_language='en',
            date_of_birth='1990-01-01'
        )
        assert profile.avatar_url == 'https://example.com/avatar.jpg'
        assert profile.bio == 'Test bio'
        assert profile.country == 'US'
        assert profile.timezone == 'America/New_York'
    
    def test_user_profile_invalid_email(self, user_id):
        """Test UserProfile with invalid email."""
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(
                pk=f'USER#{user_id}',
                sk='PROFILE',
                user_id=user_id,
                email='invalid-email',
                name='Test User',
                entity_type='USER'
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('email',) for error in errors)
    
    def test_user_profile_empty_name(self, user_id):
        """Test UserProfile with empty name."""
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(
                pk=f'USER#{user_id}',
                sk='PROFILE',
                user_id=user_id,
                email='test@example.com',
                name='',
                entity_type='USER'
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('name',) for error in errors)
    
    def test_user_profile_name_whitespace_trimmed(self, user_id):
        """Test that UserProfile name is trimmed."""
        profile = UserProfile(
            pk=f'USER#{user_id}',
            sk='PROFILE',
            user_id=user_id,
            email='test@example.com',
            name='  Test User  ',
            entity_type='USER'
        )
        assert profile.name == 'Test User'
    
    def test_user_profile_invalid_country_code(self, user_id):
        """Test UserProfile with invalid country code."""
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(
                pk=f'USER#{user_id}',
                sk='PROFILE',
                user_id=user_id,
                email='test@example.com',
                name='Test User',
                entity_type='USER',
                country='USA'  # Should be 2 chars
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('country',) for error in errors)
    
    def test_user_profile_invalid_language_code(self, user_id):
        """Test UserProfile with invalid language code."""
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(
                pk=f'USER#{user_id}',
                sk='PROFILE',
                user_id=user_id,
                email='test@example.com',
                name='Test User',
                entity_type='USER',
                preferred_language='eng'  # Should be 2 chars
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('preferred_language',) for error in errors)
    
    def test_user_profile_account_status_enum(self, user_id):
        """Test UserProfile account status enum values."""
        for status in [AccountStatus.ACTIVE, AccountStatus.SUSPENDED, AccountStatus.DELETED]:
            profile = UserProfile(
                pk=f'USER#{user_id}',
                sk='PROFILE',
                user_id=user_id,
                email='test@example.com',
                name='Test User',
                entity_type='USER',
                account_status=status
            )
            assert profile.account_status == status
    
    def test_user_profile_to_dynamodb_item(self, user_id):
        """Test converting UserProfile to DynamoDB item."""
        profile = UserProfile(
            pk=f'USER#{user_id}',
            sk='PROFILE',
            user_id=user_id,
            email='test@example.com',
            name='Test User',
            entity_type='USER'
        )
        item = profile.to_dynamodb_item()
        
        assert item['user_id'] == user_id
        assert item['email'] == 'test@example.com'
        assert item['name'] == 'Test User'
        assert item['account_status'] == 'ACTIVE'


class TestUserPreferences:
    """Test cases for UserPreferences model."""
    
    def test_user_preferences_creation(self, user_id):
        """Test creating a UserPreferences instance."""
        prefs = UserPreferences(
            pk=f'USER#{user_id}',
            sk='PREFERENCES',
            entity_type='USER_PREFERENCES'
        )
        assert prefs.email_notifications_enabled is True
        assert prefs.push_notifications_enabled is True
        assert prefs.sms_notifications_enabled is False
        assert prefs.profile_visibility == ProfileVisibility.PUBLIC
    
    def test_user_preferences_all_fields(self, user_id):
        """Test UserPreferences with all fields customized."""
        prefs = UserPreferences(
            pk=f'USER#{user_id}',
            sk='PREFERENCES',
            entity_type='USER_PREFERENCES',
            email_notifications_enabled=False,
            push_notifications_enabled=False,
            sms_notifications_enabled=True,
            marketing_emails_enabled=True,
            league_invites_enabled=False,
            friend_requests_enabled=False,
            profile_visibility=ProfileVisibility.PRIVATE,
            show_real_name=False,
            show_email=True,
            show_statistics=False,
            theme_preference=ThemePreference.DARK,
            notification_frequency=NotificationFrequency.WEEKLY,
            preferred_game_type=GameType.LAST_MAN_STANDING,
            auto_join_leagues=True
        )
        assert prefs.email_notifications_enabled is False
        assert prefs.profile_visibility == ProfileVisibility.PRIVATE
        assert prefs.theme_preference == ThemePreference.DARK
        assert prefs.preferred_game_type == GameType.LAST_MAN_STANDING
    
    def test_user_preferences_enum_values(self, user_id):
        """Test UserPreferences enum values."""
        for visibility in [ProfileVisibility.PUBLIC, ProfileVisibility.FRIENDS_ONLY, ProfileVisibility.PRIVATE]:
            prefs = UserPreferences(
                pk=f'USER#{user_id}',
                sk='PREFERENCES',
                entity_type='USER_PREFERENCES',
                profile_visibility=visibility
            )
            assert prefs.profile_visibility == visibility
    
    def test_user_preferences_to_dynamodb_item(self, user_id):
        """Test converting UserPreferences to DynamoDB item."""
        prefs = UserPreferences(
            pk=f'USER#{user_id}',
            sk='PREFERENCES',
            entity_type='USER_PREFERENCES'
        )
        item = prefs.to_dynamodb_item()
        
        assert item['email_notifications_enabled'] is True
        assert item['profile_visibility'] == 'PUBLIC'
        assert item['theme_preference'] == 'AUTO'


class TestUserSettings:
    """Test cases for UserSettings model."""
    
    def test_user_settings_creation(self, user_id):
        """Test creating a UserSettings instance."""
        settings = UserSettings(
            pk=f'USER#{user_id}',
            sk='SETTINGS',
            entity_type='USER_SETTINGS'
        )
        assert settings.two_factor_enabled is False
        assert settings.session_timeout_minutes == 30
        assert settings.ip_whitelist_enabled is False
        assert settings.api_keys_enabled is False
    
    def test_user_settings_with_2fa(self, user_id):
        """Test UserSettings with 2FA enabled."""
        from python.models.user import TwoFactorMethod
        
        settings = UserSettings(
            pk=f'USER#{user_id}',
            sk='SETTINGS',
            entity_type='USER_SETTINGS',
            two_factor_enabled=True,
            two_factor_method=TwoFactorMethod.TOTP
        )
        assert settings.two_factor_enabled is True
        assert settings.two_factor_method == TwoFactorMethod.TOTP
    
    def test_user_settings_invalid_timeout(self, user_id):
        """Test UserSettings with invalid session timeout."""
        with pytest.raises(ValidationError) as exc_info:
            UserSettings(
                pk=f'USER#{user_id}',
                sk='SETTINGS',
                entity_type='USER_SETTINGS',
                session_timeout_minutes=0
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('session_timeout_minutes',) for error in errors)
    
    def test_user_settings_negative_timeout(self, user_id):
        """Test UserSettings with negative session timeout."""
        with pytest.raises(ValidationError) as exc_info:
            UserSettings(
                pk=f'USER#{user_id}',
                sk='SETTINGS',
                entity_type='USER_SETTINGS',
                session_timeout_minutes=-30
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('session_timeout_minutes',) for error in errors)
    
    def test_user_settings_ip_whitelist(self, user_id):
        """Test UserSettings with IP whitelist."""
        settings = UserSettings(
            pk=f'USER#{user_id}',
            sk='SETTINGS',
            entity_type='USER_SETTINGS',
            ip_whitelist=['192.168.1.1', '10.0.0.1'],
            ip_whitelist_enabled=True
        )
        assert len(settings.ip_whitelist) == 2
        assert '192.168.1.1' in settings.ip_whitelist
    
    def test_user_settings_account_deletion(self, user_id):
        """Test UserSettings with account deletion."""
        deletion_date = datetime.utcnow()
        settings = UserSettings(
            pk=f'USER#{user_id}',
            sk='SETTINGS',
            entity_type='USER_SETTINGS',
            account_deletion_requested=True,
            account_deletion_date=deletion_date
        )
        assert settings.account_deletion_requested is True
        assert settings.account_deletion_date == deletion_date


class TestUserStatistics:
    """Test cases for UserStatistics model."""
    
    def test_user_statistics_creation(self, user_id, league_id):
        """Test creating a UserStatistics instance."""
        stats = UserStatistics(
            pk=f'USER#{user_id}',
            sk=f'STATISTICS#{league_id}',
            user_id=user_id,
            league_id=league_id,
            game_type=GameType.POINTS_BASED,
            entity_type='USER_STATISTICS'
        )
        assert stats.user_id == user_id
        assert stats.league_id == league_id
        assert stats.total_points == 0
        assert stats.games_played == 0
    
    def test_user_statistics_with_points(self, user_id, league_id):
        """Test UserStatistics with points data."""
        stats = UserStatistics(
            pk=f'USER#{user_id}',
            sk=f'STATISTICS#{league_id}',
            user_id=user_id,
            league_id=league_id,
            game_type=GameType.POINTS_BASED,
            entity_type='USER_STATISTICS',
            total_points=500,
            current_rank=3,
            previous_rank=5,
            games_played=20,
            highest_score=150,
            lowest_score=10
        )
        assert stats.total_points == 500
        assert stats.current_rank == 3
        assert stats.rank_change == 2  # previous - current
    
    def test_user_statistics_rank_change_calculation(self, user_id, league_id):
        """Test that rank change is calculated correctly."""
        stats = UserStatistics(
            pk=f'USER#{user_id}',
            sk=f'STATISTICS#{league_id}',
            user_id=user_id,
            league_id=league_id,
            game_type=GameType.POINTS_BASED,
            entity_type='USER_STATISTICS',
            current_rank=5,
            previous_rank=8
        )
        assert stats.rank_change == 3  # Improved by 3 positions
    
    def test_user_statistics_win_percentage_calculation(self, user_id, league_id):
        """Test that win percentage is calculated correctly."""
        stats = UserStatistics(
            pk=f'USER#{user_id}',
            sk=f'STATISTICS#{league_id}',
            user_id=user_id,
            league_id=league_id,
            game_type=GameType.LAST_MAN_STANDING,
            entity_type='USER_STATISTICS',
            games_won=7,
            games_played=10
        )
        assert stats.win_percentage == 70.0
    
    def test_user_statistics_average_points_calculation(self, user_id, league_id):
        """Test that average points per game is calculated correctly."""
        stats = UserStatistics(
            pk=f'USER#{user_id}',
            sk=f'STATISTICS#{league_id}',
            user_id=user_id,
            league_id=league_id,
            game_type=GameType.POINTS_BASED,
            entity_type='USER_STATISTICS',
            total_points=500,
            games_played=20
        )
        assert stats.average_points_per_game == 25.0
    
    def test_user_statistics_prediction_accuracy_calculation(self, user_id, league_id):
        """Test that prediction accuracy is calculated correctly."""
        stats = UserStatistics(
            pk=f'USER#{user_id}',
            sk=f'STATISTICS#{league_id}',
            user_id=user_id,
            league_id=league_id,
            game_type=GameType.POINTS_BASED,
            entity_type='USER_STATISTICS',
            total_predictions=100,
            correct_predictions=75
        )
        assert stats.prediction_accuracy == 75.0
    
    def test_user_statistics_with_lms_data(self, user_id, league_id):
        """Test UserStatistics with Last Man Standing data."""
        stats = UserStatistics(
            pk=f'USER#{user_id}',
            sk=f'STATISTICS#{league_id}',
            user_id=user_id,
            league_id=league_id,
            game_type=GameType.LAST_MAN_STANDING,
            entity_type='USER_STATISTICS',
            games_won=15,
            games_lost=5,
            consecutive_wins=3,
            best_consecutive_wins=7
        )
        assert stats.games_won == 15
        assert stats.games_lost == 5
        assert stats.consecutive_wins == 3
        assert stats.best_consecutive_wins == 7
    
    def test_user_statistics_non_negative_values(self, user_id, league_id):
        """Test that UserStatistics enforces non-negative values."""
        with pytest.raises(ValidationError):
            UserStatistics(
                pk=f'USER#{user_id}',
                sk=f'STATISTICS#{league_id}',
                user_id=user_id,
                league_id=league_id,
                game_type=GameType.POINTS_BASED,
                entity_type='USER_STATISTICS',
                total_points=-100  # Invalid
            )
    
    def test_user_statistics_to_dynamodb_item(self, user_id, league_id):
        """Test converting UserStatistics to DynamoDB item."""
        stats = UserStatistics(
            pk=f'USER#{user_id}',
            sk=f'STATISTICS#{league_id}',
            user_id=user_id,
            league_id=league_id,
            game_type=GameType.POINTS_BASED,
            entity_type='USER_STATISTICS',
            total_points=500,
            games_played=20
        )
        item = stats.to_dynamodb_item()
        
        assert item['user_id'] == user_id
        assert item['league_id'] == league_id
        assert item['total_points'] == 500
        assert item['game_type'] == 'POINTS_BASED'


class TestUserProfileResponse:
    """Test cases for UserProfileResponse model."""
    
    def test_user_profile_response_creation(self, user_id):
        """Test creating a UserProfileResponse instance."""
        response = UserProfileResponse(
            user_id=user_id,
            email='test@example.com',
            name='Test User',
            account_status='ACTIVE',
            created_at='2024-01-01T00:00:00',
            updated_at='2024-01-01T00:00:00'
        )
        assert response.user_id == user_id
        assert response.email == 'test@example.com'
        assert response.name == 'Test User'
    
    def test_user_profile_response_with_optional_fields(self, user_id):
        """Test UserProfileResponse with optional fields."""
        response = UserProfileResponse(
            user_id=user_id,
            email='test@example.com',
            name='Test User',
            avatar_url='https://example.com/avatar.jpg',
            bio='Test bio',
            country='US',
            timezone='America/New_York',
            account_status='ACTIVE',
            created_at='2024-01-01T00:00:00',
            updated_at='2024-01-01T00:00:00'
        )
        assert response.avatar_url == 'https://example.com/avatar.jpg'
        assert response.bio == 'Test bio'


class TestUserStatisticsResponse:
    """Test cases for UserStatisticsResponse model."""
    
    def test_user_statistics_response_creation(self, user_id, league_id):
        """Test creating a UserStatisticsResponse instance."""
        response = UserStatisticsResponse(
            user_id=user_id,
            league_id=league_id,
            game_type='POINTS_BASED',
            current_rank=5,
            total_points=500,
            games_played=20,
            average_points_per_game=25.0,
            prediction_accuracy=75.0,
            joined_at='2024-01-01T00:00:00',
            updated_at='2024-01-01T00:00:00'
        )
        assert response.user_id == user_id
        assert response.league_id == league_id
        assert response.current_rank == 5
        assert response.total_points == 500
