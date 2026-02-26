"""League repository for DynamoDB operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from aws_lambda_powertools import Logger
from .table import DynamoDBTable
from ..utils.exceptions import NotFoundError, ValidationError

logger = Logger()


class LeagueRepository:
    """Repository for league-related DynamoDB operations.
    
    Handles all league operations including creation, retrieval, member management,
    and game associations. Uses single-table design with item collections.
    
    Access Patterns:
    - Pattern #3: Create league
    - Pattern #4: Get league details
    - Pattern #5: Get league members
    - Pattern #6: Add member to league
    - Pattern #7: Get league's games
    """
    
    def __init__(self, table: Optional[DynamoDBTable] = None):
        """Initialize league repository.
        
        Args:
            table: DynamoDBTable instance (creates new if not provided)
        """
        self.table = table or DynamoDBTable()
    
    # League Metadata Operations
    
    def create_league(self, league_id: str, name: str, owner_id: str, 
                     description: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create a new league.
        
        Args:
            league_id: Unique league identifier (UUID)
            name: League name
            owner_id: User ID of league owner
            description: Optional league description
            **kwargs: Additional attributes (game_type, rules, etc.)
            
        Returns:
            Created league item
            
        Raises:
            ValidationError: If required fields are missing or invalid
        """
        if not league_id or not name or not owner_id:
            raise ValidationError("league_id, name, and owner_id are required")
        
        now = datetime.utcnow().isoformat()
        
        item = {
            'PK': f'LEAGUE#{league_id}',
            'SK': 'METADATA',
            'entity_type': 'LEAGUE',
            'league_id': league_id,
            'name': name,
            'owner_id': owner_id,
            'description': description,
            'member_count': 1,  # Owner is first member
            'game_count': 0,
            'status': 'ACTIVE',
            'created_at': now,
            'updated_at': now,
            **kwargs
        }
        
        self.table.put_item(item)
        
        # Add owner as league member
        self._add_member_item(league_id, owner_id, 'OWNER', now)
        
        logger.info(f"Created league: {league_id} by owner {owner_id}")
        return item
    
    def get_league(self, league_id: str) -> Optional[Dict[str, Any]]:
        """Get league details by ID.
        
        Args:
            league_id: League ID
            
        Returns:
            League metadata item or None if not found
        """
        return self.table.get_item(f'LEAGUE#{league_id}', 'METADATA')
    
    def update_league(self, league_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update league metadata.
        
        Args:
            league_id: League ID
            updates: Dictionary of attributes to update
            
        Returns:
            Updated league item
        """
        updates['updated_at'] = datetime.utcnow().isoformat()
        result = self.table.update_item(f'LEAGUE#{league_id}', 'METADATA', updates)
        logger.info(f"Updated league: {league_id}")
        return result
    
    def delete_league(self, league_id: str) -> None:
        """Delete a league (soft delete - mark as inactive).
        
        Args:
            league_id: League ID
        """
        self.update_league(league_id, {'status': 'INACTIVE'})
        logger.info(f"Deleted league: {league_id}")
    
    # Member Operations
    
    def add_member(self, league_id: str, user_id: str, role: str = 'MEMBER') -> Dict[str, Any]:
        """Add a member to a league.
        
        Args:
            league_id: League ID
            user_id: User ID to add
            role: Member role (OWNER, ADMIN, MEMBER)
            
        Returns:
            Created member item
        """
        now = datetime.utcnow().isoformat()
        
        # Add member to league
        member_item = self._add_member_item(league_id, user_id, role, now)
        
        # Update league member count
        league = self.get_league(league_id)
        if league:
            new_count = league.get('member_count', 0) + 1
            self.update_league(league_id, {'member_count': new_count})
        
        # Add league to user's leagues
        user_item = {
            'PK': f'USER#{user_id}',
            'SK': f'LEAGUE#{league_id}',
            'entity_type': 'USER_LEAGUE',
            'league_id': league_id,
            'role': role,
            'joined_at': now,
            'created_at': now,
            'updated_at': now
        }
        self.table.put_item(user_item)
        
        logger.info(f"Added member {user_id} to league {league_id} with role {role}")
        return member_item
    
    def remove_member(self, league_id: str, user_id: str) -> None:
        """Remove a member from a league.
        
        Args:
            league_id: League ID
            user_id: User ID to remove
        """
        # Remove member from league
        self.table.delete_item(f'LEAGUE#{league_id}', f'MEMBER#{user_id}')
        
        # Remove league from user's leagues
        self.table.delete_item(f'USER#{user_id}', f'LEAGUE#{league_id}')
        
        # Update league member count
        league = self.get_league(league_id)
        if league:
            new_count = max(0, league.get('member_count', 1) - 1)
            self.update_league(league_id, {'member_count': new_count})
        
        logger.info(f"Removed member {user_id} from league {league_id}")
    
    def get_members(self, league_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all members of a league.
        
        Args:
            league_id: League ID
            limit: Maximum number of members to return
            
        Returns:
            List of member items
        """
        items = self.table.query(f'LEAGUE#{league_id}', 'MEMBER#')
        return items[:limit] if limit else items
    
    def get_member(self, league_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific league member.
        
        Args:
            league_id: League ID
            user_id: User ID
            
        Returns:
            Member item or None if not found
        """
        return self.table.get_item(f'LEAGUE#{league_id}', f'MEMBER#{user_id}')
    
    def update_member_role(self, league_id: str, user_id: str, role: str) -> Dict[str, Any]:
        """Update a member's role in the league.
        
        Args:
            league_id: League ID
            user_id: User ID
            role: New role (OWNER, ADMIN, MEMBER)
            
        Returns:
            Updated member item
        """
        result = self.table.update_item(
            f'LEAGUE#{league_id}',
            f'MEMBER#{user_id}',
            {'role': role, 'updated_at': datetime.utcnow().isoformat()}
        )
        logger.info(f"Updated member {user_id} role in league {league_id} to {role}")
        return result
    
    # Game Operations
    
    def add_game(self, league_id: str, game_id: str) -> Dict[str, Any]:
        """Add a game to a league.
        
        Args:
            league_id: League ID
            game_id: Game ID
            
        Returns:
            Created game association item
        """
        now = datetime.utcnow().isoformat()
        
        item = {
            'PK': f'LEAGUE#{league_id}',
            'SK': f'GAME#{game_id}',
            'entity_type': 'LEAGUE_GAME',
            'league_id': league_id,
            'game_id': game_id,
            'created_at': now,
            'updated_at': now
        }
        
        self.table.put_item(item)
        
        # Update league game count
        league = self.get_league(league_id)
        if league:
            new_count = league.get('game_count', 0) + 1
            self.update_league(league_id, {'game_count': new_count})
        
        logger.info(f"Added game {game_id} to league {league_id}")
        return item
    
    def get_games(self, league_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all games in a league.
        
        Args:
            league_id: League ID
            limit: Maximum number of games to return
            
        Returns:
            List of game items
        """
        items = self.table.query(f'LEAGUE#{league_id}', 'GAME#')
        return items[:limit] if limit else items
    
    def remove_game(self, league_id: str, game_id: str) -> None:
        """Remove a game from a league.
        
        Args:
            league_id: League ID
            game_id: Game ID
        """
        self.table.delete_item(f'LEAGUE#{league_id}', f'GAME#{game_id}')
        
        # Update league game count
        league = self.get_league(league_id)
        if league:
            new_count = max(0, league.get('game_count', 1) - 1)
            self.update_league(league_id, {'game_count': new_count})
        
        logger.info(f"Removed game {game_id} from league {league_id}")
    
    # Standings Operations
    
    def get_standings(self, league_id: str, game_type: str, round_number: int) -> Optional[Dict[str, Any]]:
        """Get league standings for a specific round.
        
        Args:
            league_id: League ID
            game_type: Game type (POINTS_BASED, LAST_MAN_STANDING)
            round_number: Round number
            
        Returns:
            Standings item or None if not found
        """
        return self.table.get_item(
            f'LEAGUE#{league_id}',
            f'STANDINGS#{game_type}#{round_number}'
        )
    
    def get_final_standings(self, league_id: str, game_type: str) -> Optional[Dict[str, Any]]:
        """Get final standings for a league.
        
        Args:
            league_id: League ID
            game_type: Game type (POINTS_BASED, LAST_MAN_STANDING)
            
        Returns:
            Final standings item or None if not found
        """
        return self.table.get_item(
            f'LEAGUE#{league_id}',
            f'STANDINGS#{game_type}#FINAL'
        )
    
    # Helper Methods
    
    def _add_member_item(self, league_id: str, user_id: str, role: str, now: str) -> Dict[str, Any]:
        """Internal helper to create a member item.
        
        Args:
            league_id: League ID
            user_id: User ID
            role: Member role
            now: Current timestamp
            
        Returns:
            Created member item
        """
        item = {
            'PK': f'LEAGUE#{league_id}',
            'SK': f'MEMBER#{user_id}',
            'entity_type': 'LEAGUE_MEMBER',
            'league_id': league_id,
            'user_id': user_id,
            'role': role,
            'joined_at': now,
            'created_at': now,
            'updated_at': now
        }
        self.table.put_item(item)
        return item
    
    def get_user_leagues(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all leagues for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of leagues to return
            
        Returns:
            List of user league items
        """
        items = self.table.query(f'USER#{user_id}', 'LEAGUE#')
        return items[:limit] if limit else items
    
    def is_member(self, league_id: str, user_id: str) -> bool:
        """Check if a user is a member of a league.
        
        Args:
            league_id: League ID
            user_id: User ID
            
        Returns:
            True if user is a member, False otherwise
        """
        member = self.get_member(league_id, user_id)
        return member is not None
