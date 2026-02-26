"""User entity models for DynamoDB."""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, validator
from .base import BaseEntity


class AccountStatus(str, Enum):
    """User account status."""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class ProfileVisibility(str, Enum):
    """User profile visibility level."""
    PUBLIC = "PUBLIC"
    FRIENDS_ONLY = "FRIENDS_ONLY"
    PRIVATE = "PRIVATE"


class ThemePreference(str, Enum):
    """UI theme preference."""
    LIGHT = "LIGHT"
    DARK = "DARK"
    AUTO = "AUTO"


class NotificationFrequency(str, Enum):
    """Notification frequency preference."""
    INSTANT = "INSTANT"
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"


class GameType(str, Enum):
    """Competition game type."""
    POINTS_BASED = "POINTS_BASED"
    LAST_MAN_STANDING = "LAST_MAN_STANDING"
    BOTH = "BOTH"


class TwoFactorMethod(str, Enum):
    """Two-factor authentication method."""
    TOTP = "TOTP"
    SMS = "SMS"
    EMAIL = "EMAIL"


class UserProfile(BaseEntity):
    """User profile entity."""
    
    user_id: str = Field(..., description="Unique user identifier (UUID v4)")
    email: EmailStr = Field(..., description="User email address")
    email_verified: bool = Field(default=False, description="Email verification status")
    name: str = Field(..., min_length=1, max_length=100, description="User display name")
    avatar_url: Optional[str] = Field(None, max_length=500, description="User profile picture URL")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    phone_number: Optional[str] = Field(None, description="User phone number (E.164 format)")
    country: Optional[str] = Field(None, description="User country code (ISO 3166-1 alpha-2)")
    timezone: Optional[str] = Field(None, description="User timezone (IANA format)")
    preferred_language: Optional[str] = Field(None, description="User language preference (ISO 639-1)")
    date_of_birth: Optional[str] = Field(None, description="User birth date (ISO 8601)")
    account_status: AccountStatus = Field(default=AccountStatus.ACTIVE, description="Account status")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    login_count: int = Field(default=0, description="Total login count")
    cognito_sub: Optional[str] = Field(None, description="Cognito subject identifier")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate name format."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
    
    @validator('country')
    def validate_country(cls, v):
        """Validate country code format."""
        if v and len(v) != 2:
            raise ValueError("Country code must be ISO 3166-1 alpha-2 (2 characters)")
        return v
    
    @validator('preferred_language')
    def validate_language(cls, v):
        """Validate language code format."""
        if v and len(v) != 2:
            raise ValueError("Language code must be ISO 639-1 (2 characters)")
        return v
    
    class Config:
        use_enum_values = True


class UserPreferences(BaseEntity):
    """User preferences entity."""
    
    email_notifications_enabled: bool = Field(default=True)
    push_notifications_enabled: bool = Field(default=True)
    sms_notifications_enabled: bool = Field(default=False)
    marketing_emails_enabled: bool = Field(default=False)
    league_invites_enabled: bool = Field(default=True)
    friend_requests_enabled: bool = Field(default=True)
    profile_visibility: ProfileVisibility = Field(default=ProfileVisibility.PUBLIC)
    show_real_name: bool = Field(default=True)
    show_email: bool = Field(default=False)
    show_statistics: bool = Field(default=True)
    theme_preference: ThemePreference = Field(default=ThemePreference.AUTO)
    notification_frequency: NotificationFrequency = Field(default=NotificationFrequency.DAILY)
    preferred_game_type: GameType = Field(default=GameType.BOTH)
    auto_join_leagues: bool = Field(default=False)
    
    class Config:
        use_enum_values = True


class UserSettings(BaseEntity):
    """User account settings entity."""
    
    two_factor_enabled: bool = Field(default=False)
    two_factor_method: Optional[TwoFactorMethod] = Field(None)
    password_changed_at: Optional[datetime] = Field(None)
    password_expiry_days: Optional[int] = Field(None)
    session_timeout_minutes: int = Field(default=30)
    ip_whitelist: List[str] = Field(default_factory=list)
    ip_whitelist_enabled: bool = Field(default=False)
    api_keys_enabled: bool = Field(default=False)
    data_export_enabled: bool = Field(default=True)
    account_deletion_requested: bool = Field(default=False)
    account_deletion_date: Optional[datetime] = Field(None)
    
    @validator('session_timeout_minutes')
    def validate_timeout(cls, v):
        """Validate session timeout."""
        if v <= 0:
            raise ValueError("Session timeout must be positive")
        return v
    
    class Config:
        use_enum_values = True


class UserStatistics(BaseEntity):
    """User statistics per league entity."""
    
    user_id: str = Field(..., description="User identifier")
    league_id: str = Field(..., description="League identifier")
    game_type: GameType = Field(..., description="Competition type")
    
    # Points-based stats
    total_points: int = Field(default=0, ge=0)
    current_rank: int = Field(default=0, ge=0)
    previous_rank: int = Field(default=0, ge=0)
    rank_change: int = Field(default=0)
    games_played: int = Field(default=0, ge=0)
    average_points_per_game: float = Field(default=0.0, ge=0)
    highest_score: int = Field(default=0, ge=0)
    lowest_score: int = Field(default=0, ge=0)
    
    # Last Man Standing stats
    games_won: int = Field(default=0, ge=0)
    games_lost: int = Field(default=0, ge=0)
    win_percentage: float = Field(default=0.0, ge=0, le=100)
    consecutive_wins: int = Field(default=0, ge=0)
    consecutive_losses: int = Field(default=0, ge=0)
    best_consecutive_wins: int = Field(default=0, ge=0)
    
    # Prediction stats
    total_predictions: int = Field(default=0, ge=0)
    correct_predictions: int = Field(default=0, ge=0)
    prediction_accuracy: float = Field(default=0.0, ge=0, le=100)
    
    # Timestamps
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: Optional[datetime] = Field(None)
    
    @validator('rank_change', pre=True, always=True)
    def calculate_rank_change(cls, v, values):
        """Calculate rank change from previous and current rank."""
        if 'previous_rank' in values and 'current_rank' in values:
            prev = values.get('previous_rank', 0)
            curr = values.get('current_rank', 0)
            if prev > 0 and curr > 0:
                return prev - curr
        return v
    
    @validator('win_percentage', pre=True, always=True)
    def calculate_win_percentage(cls, v, values):
        """Calculate win percentage from wins and losses."""
        if 'games_won' in values and 'games_played' in values:
            won = values.get('games_won', 0)
            played = values.get('games_played', 0)
            if played > 0:
                return round((won / played) * 100, 2)
        return v
    
    @validator('average_points_per_game', pre=True, always=True)
    def calculate_avg_points(cls, v, values):
        """Calculate average points per game."""
        if 'total_points' in values and 'games_played' in values:
            points = values.get('total_points', 0)
            played = values.get('games_played', 0)
            if played > 0:
                return round(points / played, 2)
        return v
    
    @validator('prediction_accuracy', pre=True, always=True)
    def calculate_prediction_accuracy(cls, v, values):
        """Calculate prediction accuracy percentage."""
        if 'correct_predictions' in values and 'total_predictions' in values:
            correct = values.get('correct_predictions', 0)
            total = values.get('total_predictions', 0)
            if total > 0:
                return round((correct / total) * 100, 2)
        return v
    
    class Config:
        use_enum_values = True


class UserProfileResponse(BaseModel):
    """User profile response model."""
    
    user_id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    account_status: str
    created_at: str
    updated_at: str


class UserStatisticsResponse(BaseModel):
    """User statistics response model."""
    
    user_id: str
    league_id: str
    game_type: str
    current_rank: int
    total_points: int
    games_played: int
    average_points_per_game: float
    prediction_accuracy: float
    joined_at: str
    updated_at: str
