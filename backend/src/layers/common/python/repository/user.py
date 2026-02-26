"""User repository for DynamoDB operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from aws_lambda_powertools import Logger
from .table import DynamoDBTable
from ..models.user import UserProfile, UserPreferences, UserSettings, UserStatistics

logger = Logger()


class UserRepository:
    """Repository for user-related DynamoDB operations."""
    
    def __init__(self, table: Optional[DynamoDBTable] = None):
        """Initialize user repository.
        
        Args:
            table: DynamoDBTable instance (creates new if not provided)
        """
        self.table = table or DynamoDBTable()
    
    # Profile Operations
    
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID.
        
        Args:
            user_id: User ID (UUID)
            
        Returns:
            User profile item or None if not found
        """
        return self.table.get_item(f'USER#{user_id}', 'PROFILE')
    
    def create_profile(self, profile: UserProfile) -> None:
        """Create new user profile.
        
        Args:
            profile: UserProfile instance
        """
        item = profile.dict(exclude_none=True)
        item['PK'] = f'USER#{profile.user_id}'
        item['SK'] = 'PROFILE'
        item['entity_type'] = 'USER'
        self.table.put_item(item)
        logger.info(f"Created user profile: {profile.user_id}")
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile.
        
        Args:
            user_id: User ID (UUID)
            updates: Dictionary of attributes to update
            
        Returns:
            Updated profile item
        """
        updates['updated_at'] = datetime.utcnow().isoformat()
        result = self.table.update_item(f'USER#{user_id}', 'PROFILE', updates)
        logger.info(f"Updated user profile: {user_id}")
        return result
    
    # Preferences Operations
    
    def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences by ID.
        
        Args:
            user_id: User ID (UUID)
            
        Returns:
            User preferences item or None if not found
        """
        return self.table.get_item(f'USER#{user_id}', 'PREFERENCES')
    
    def create_preferences(self, user_id: str, preferences: UserPreferences) -> None:
        """Create user preferences.
        
        Args:
            user_id: User ID (UUID)
            preferences: UserPreferences instance
        """
        item = preferences.dict(exclude_none=True)
        item['PK'] = f'USER#{user_id}'
        item['SK'] = 'PREFERENCES'
        item['entity_type'] = 'USER_PREFERENCES'
        self.table.put_item(item)
        logger.info(f"Created user preferences: {user_id}")
    
    def update_preferences(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences.
        
        Args:
            user_id: User ID (UUID)
            updates: Dictionary of attributes to update
            
        Returns:
            Updated preferences item
        """
        updates['updated_at'] = datetime.utcnow().isoformat()
        result = self.table.update_item(f'USER#{user_id}', 'PREFERENCES', updates)
        logger.info(f"Updated user preferences: {user_id}")
        return result
    
    # Settings Operations
    
    def get_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user settings by ID.
        
        Args:
            user_id: User ID (UUID)
            
        Returns:
            User settings item or None if not found
        """
        return self.table.get_item(f'USER#{user_id}', 'SETTINGS')
    
    def create_settings(self, user_id: str, settings: UserSettings) -> None:
        """Create user settings.
        
        Args:
            user_id: User ID (UUID)
            settings: UserSettings instance
        """
        item = settings.dict(exclude_none=True)
        item['PK'] = f'USER#{user_id}'
        item['SK'] = 'SETTINGS'
        item['entity_type'] = 'USER_SETTINGS'
        self.table.put_item(item)
        logger.info(f"Created user settings: {user_id}")
    
    def update_settings(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user settings.
        
        Args:
            user_id: User ID (UUID)
            updates: Dictionary of attributes to update
            
        Returns:
            Updated settings item
        """
        updates['updated_at'] = datetime.utcnow().isoformat()
        result = self.table.update_item(f'USER#{user_id}', 'SETTINGS', updates)
        logger.info(f"Updated user settings: {user_id}")
        return result
    
    # Statistics Operations
    
    def get_statistics(self, user_id: str, league_id: str) -> Optional[Dict[str, Any]]:
        """Get user statistics for a specific league.
        
        Args:
            user_id: User ID (UUID)
            league_id: League ID
            
        Returns:
            User statistics item or None if not found
        """
        return self.table.get_item(f'USER#{user_id}', f'STATISTICS#{league_id}')
    
    def get_all_statistics(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all statistics for a user across all leagues.
        
        Args:
            user_id: User ID (UUID)
            
        Returns:
            List of statistics items
        """
        return self.table.query(f'USER#{user_id}', 'STATISTICS#')
    
    def create_statistics(self, statistics: UserStatistics) -> None:
        """Create user statistics for a league.
        
        Args:
            statistics: UserStatistics instance
        """
        item = statistics.dict(exclude_none=True)
        item['PK'] = f'USER#{statistics.user_id}'
        item['SK'] = f'STATISTICS#{statistics.league_id}'
        item['GSI1PK'] = f'USER#{statistics.user_id}'
        item['GSI1SK'] = f'STAT#{statistics.league_id}'
        item['entity_type'] = 'USER_STATISTICS'
        self.table.put_item(item)
        logger.info(f"Created statistics for user {statistics.user_id} in league {statistics.league_id}")
    
    def update_statistics(self, user_id: str, league_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user statistics for a league.
        
        Args:
            user_id: User ID (UUID)
            league_id: League ID
            updates: Dictionary of attributes to update
            
        Returns:
            Updated statistics item
        """
        updates['updated_at'] = datetime.utcnow().isoformat()
        result = self.table.update_item(f'USER#{user_id}', f'STATISTICS#{league_id}', updates)
        logger.info(f"Updated statistics for user {user_id} in league {league_id}")
        return result
    
    # Batch Operations
    
    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """Get all user data (profile, preferences, settings, statistics).
        
        Args:
            user_id: User ID (UUID)
            
        Returns:
            Dictionary with all user data
        """
        items = self.table.query(f'USER#{user_id}')
        
        user_data = {
            'profile': None,
            'preferences': None,
            'settings': None,
            'statistics': []
        }
        
        for item in items:
            sk = item.get('SK', '')
            if sk == 'PROFILE':
                user_data['profile'] = item
            elif sk == 'PREFERENCES':
                user_data['preferences'] = item
            elif sk == 'SETTINGS':
                user_data['settings'] = item
            elif sk.startswith('STATISTICS#'):
                user_data['statistics'].append(item)
        
        return user_data
    
    def create_user_complete(self, profile: UserProfile, preferences: UserPreferences, 
                            settings: UserSettings) -> None:
        """Create complete user profile with preferences and settings.
        
        Args:
            profile: UserProfile instance
            preferences: UserPreferences instance
            settings: UserSettings instance
        """
        items = []
        
        # Profile item
        profile_item = profile.dict(exclude_none=True)
        profile_item['PK'] = f'USER#{profile.user_id}'
        profile_item['SK'] = 'PROFILE'
        profile_item['entity_type'] = 'USER'
        items.append(profile_item)
        
        # Preferences item
        prefs_item = preferences.dict(exclude_none=True)
        prefs_item['PK'] = f'USER#{profile.user_id}'
        prefs_item['SK'] = 'PREFERENCES'
        prefs_item['entity_type'] = 'USER_PREFERENCES'
        items.append(prefs_item)
        
        # Settings item
        settings_item = settings.dict(exclude_none=True)
        settings_item['PK'] = f'USER#{profile.user_id}'
        settings_item['SK'] = 'SETTINGS'
        settings_item['entity_type'] = 'USER_SETTINGS'
        items.append(settings_item)
        
        # Batch write
        with self.table.table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)
        
        logger.info(f"Created complete user profile: {profile.user_id}")
    
    # Utility Operations
    
    def delete_user(self, user_id: str) -> None:
        """Delete all user data (soft delete - mark as deleted).
        
        Args:
            user_id: User ID (UUID)
        """
        # Mark profile as deleted
        self.update_profile(user_id, {
            'account_status': 'DELETED',
            'account_deletion_date': datetime.utcnow().isoformat()
        })
        logger.info(f"Marked user as deleted: {user_id}")
    
    def suspend_user(self, user_id: str) -> None:
        """Suspend user account.
        
        Args:
            user_id: User ID (UUID)
        """
        self.update_profile(user_id, {'account_status': 'SUSPENDED'})
        logger.info(f"Suspended user: {user_id}")
    
    def reactivate_user(self, user_id: str) -> None:
        """Reactivate suspended user account.
        
        Args:
            user_id: User ID (UUID)
        """
        self.update_profile(user_id, {'account_status': 'ACTIVE'})
        logger.info(f"Reactivated user: {user_id}")
    
    def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp.
        
        Args:
            user_id: User ID (UUID)
        """
        now = datetime.utcnow().isoformat()
        profile = self.get_profile(user_id)
        if profile:
            login_count = profile.get('login_count', 0) + 1
            self.update_profile(user_id, {
                'last_login_at': now,
                'login_count': login_count
            })
