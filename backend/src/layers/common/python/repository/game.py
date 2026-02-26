"""Game repository for DynamoDB operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from aws_lambda_powertools import Logger
from .table import DynamoDBTable
from ..utils.exceptions import NotFoundError, ValidationError

logger = Logger()


class GameRepository:
    """Repository for game-related DynamoDB operations.
    
    Handles all game operations including creation, retrieval, member management,
    round associations, and standings. Uses single-table design with item collections.
    
    Access Patterns:
    - Pattern #8: Create game
    - Pattern #9: Get game details
    - Pattern #10: Get game's rounds
    - Pattern #16: Get game standings
    - Pattern #20: Check if user eliminated (LMS)
    """
    
    def __init__(self, table: Optional[DynamoDBTable] = None):
        """Initialize game repository.
        
        Args:
            table: DynamoDBTable instance (creates new if not provided)
        """
        self.table = table or DynamoDBTable()
    
    # Game Metadata Operations
    
    def create_game(self, game_id: str, league_id: str, game_type: str,
                   name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create a new game.
        
        Args:
            game_id: Unique game identifier (UUID)
            league_id: Parent league ID
            game_type: Game type (POINTS_BASED, LAST_MAN_STANDING)
            name: Optional game name
            **kwargs: Additional attributes (rules, settings, etc.)
            
        Returns:
            Created game item
            
        Raises:
            ValidationError: If required fields are missing or invalid
        """
        if not game_id or not league_id or not game_type:
            raise ValidationError("game_id, league_id, and game_type are required")
        
        if game_type not in ['POINTS_BASED', 'LAST_MAN_STANDING']:
            raise ValidationError(f"Invalid game_type: {game_type}")
        
        now = datetime.utcnow().isoformat()
        
        item = {
            'PK': f'GAME#{game_id}',
            'SK': 'METADATA',
            'entity_type': 'GAME',
            'game_id': game_id,
            'league_id': league_id,
            'game_type': game_type,
            'name': name or f'{game_type} Game',
            'member_count': 0,
            'round_count': 0,
            'current_round': 0,
            'status': 'SCHEDULED',
            'created_at': now,
            'updated_at': now,
            **kwargs
        }
        
        self.table.put_item(item)
        logger.info(f"Created game: {game_id} in league {league_id}")
        return item
    
    def get_game(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get game details by ID.
        
        Args:
            game_id: Game ID
            
        Returns:
            Game metadata item or None if not found
        """
        return self.table.get_item(f'GAME#{game_id}', 'METADATA')
    
    def update_game(self, game_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update game metadata.
        
        Args:
            game_id: Game ID
            updates: Dictionary of attributes to update
            
        Returns:
            Updated game item
        """
        updates['updated_at'] = datetime.utcnow().isoformat()
        result = self.table.update_item(f'GAME#{game_id}', 'METADATA', updates)
        logger.info(f"Updated game: {game_id}")
        return result
    
    def delete_game(self, game_id: str) -> None:
        """Delete a game (soft delete - mark as cancelled).
        
        Args:
            game_id: Game ID
        """
        self.update_game(game_id, {'status': 'CANCELLED'})
        logger.info(f"Deleted game: {game_id}")
    
    # Member Operations
    
    def add_member(self, game_id: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """Add a member to a game.
        
        Args:
            game_id: Game ID
            user_id: User ID to add
            **kwargs: Additional attributes (lives_remaining, etc.)
            
        Returns:
            Created member item
        """
        now = datetime.utcnow().isoformat()
        
        item = {
            'PK': f'GAME#{game_id}',
            'SK': f'MEMBER#{user_id}',
            'entity_type': 'GAME_MEMBER',
            'game_id': game_id,
            'user_id': user_id,
            'is_eliminated': False,
            'joined_at': now,
            'created_at': now,
            'updated_at': now,
            **kwargs
        }
        
        self.table.put_item(item)
        
        # Update game member count
        game = self.get_game(game_id)
        if game:
            new_count = game.get('member_count', 0) + 1
            self.update_game(game_id, {'member_count': new_count})
        
        logger.info(f"Added member {user_id} to game {game_id}")
        return item
    
    def remove_member(self, game_id: str, user_id: str) -> None:
        """Remove a member from a game.
        
        Args:
            game_id: Game ID
            user_id: User ID to remove
        """
        self.table.delete_item(f'GAME#{game_id}', f'MEMBER#{user_id}')
        
        # Update game member count
        game = self.get_game(game_id)
        if game:
            new_count = max(0, game.get('member_count', 1) - 1)
            self.update_game(game_id, {'member_count': new_count})
        
        logger.info(f"Removed member {user_id} from game {game_id}")
    
    def get_members(self, game_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all members of a game.
        
        Args:
            game_id: Game ID
            limit: Maximum number of members to return
            
        Returns:
            List of member items
        """
        items = self.table.query(f'GAME#{game_id}', 'MEMBER#')
        return items[:limit] if limit else items
    
    def get_member(self, game_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific game member.
        
        Args:
            game_id: Game ID
            user_id: User ID
            
        Returns:
            Member item or None if not found
        """
        return self.table.get_item(f'GAME#{game_id}', f'MEMBER#{user_id}')
    
    def update_member(self, game_id: str, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a game member's attributes.
        
        Args:
            game_id: Game ID
            user_id: User ID
            updates: Dictionary of attributes to update
            
        Returns:
            Updated member item
        """
        updates['updated_at'] = datetime.utcnow().isoformat()
        result = self.table.update_item(
            f'GAME#{game_id}',
            f'MEMBER#{user_id}',
            updates
        )
        logger.info(f"Updated member {user_id} in game {game_id}")
        return result
    
    # Round Operations
    
    def add_round(self, game_id: str, round_id: str, round_number: int) -> Dict[str, Any]:
        """Add a round to a game.
        
        Args:
            game_id: Game ID
            round_id: Round ID
            round_number: Round number
            
        Returns:
            Created round association item
        """
        now = datetime.utcnow().isoformat()
        
        item = {
            'PK': f'GAME#{game_id}',
            'SK': f'ROUND#{round_id}',
            'entity_type': 'GAME_ROUND',
            'game_id': game_id,
            'round_id': round_id,
            'round_number': round_number,
            'created_at': now,
            'updated_at': now
        }
        
        self.table.put_item(item)
        
        # Update game round count and current round
        game = self.get_game(game_id)
        if game:
            new_count = game.get('round_count', 0) + 1
            updates = {'round_count': new_count}
            if round_number > game.get('current_round', 0):
                updates['current_round'] = round_number
            self.update_game(game_id, updates)
        
        logger.info(f"Added round {round_id} to game {game_id}")
        return item
    
    def get_rounds(self, game_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all rounds in a game.
        
        Args:
            game_id: Game ID
            limit: Maximum number of rounds to return
            
        Returns:
            List of round items
        """
        items = self.table.query(f'GAME#{game_id}', 'ROUND#')
        return items[:limit] if limit else items
    
    def remove_round(self, game_id: str, round_id: str) -> None:
        """Remove a round from a game.
        
        Args:
            game_id: Game ID
            round_id: Round ID
        """
        self.table.delete_item(f'GAME#{game_id}', f'ROUND#{round_id}')
        
        # Update game round count
        game = self.get_game(game_id)
        if game:
            new_count = max(0, game.get('round_count', 1) - 1)
            self.update_game(game_id, {'round_count': new_count})
        
        logger.info(f"Removed round {round_id} from game {game_id}")
    
    # Standings Operations
    
    def get_standings(self, game_id: str, game_type: str, round_number: int) -> Optional[Dict[str, Any]]:
        """Get game standings for a specific round.
        
        Args:
            game_id: Game ID
            game_type: Game type (POINTS_BASED, LAST_MAN_STANDING)
            round_number: Round number
            
        Returns:
            Standings item or None if not found
        """
        return self.table.get_item(
            f'GAME#{game_id}',
            f'STANDINGS#{game_type}#{round_number}'
        )
    
    def get_final_standings(self, game_id: str, game_type: str) -> Optional[Dict[str, Any]]:
        """Get final standings for a game.
        
        Args:
            game_id: Game ID
            game_type: Game type (POINTS_BASED, LAST_MAN_STANDING)
            
        Returns:
            Final standings item or None if not found
        """
        return self.table.get_item(
            f'GAME#{game_id}',
            f'STANDINGS#{game_type}#FINAL'
        )
    
    # LMS-Specific Operations
    
    def eliminate_member(self, game_id: str, user_id: str, round_number: int) -> Dict[str, Any]:
        """Mark a member as eliminated (Last Man Standing).
        
        Args:
            game_id: Game ID
            user_id: User ID
            round_number: Round number when eliminated
            
        Returns:
            Updated member item
        """
        result = self.update_member(
            game_id,
            user_id,
            {
                'is_eliminated': True,
                'eliminated_round': round_number,
                'eliminated_at': datetime.utcnow().isoformat()
            }
        )
        logger.info(f"Eliminated member {user_id} from game {game_id} in round {round_number}")
        return result
    
    def is_eliminated(self, game_id: str, user_id: str) -> bool:
        """Check if a member is eliminated (Last Man Standing).
        
        Args:
            game_id: Game ID
            user_id: User ID
            
        Returns:
            True if eliminated, False otherwise
        """
        member = self.get_member(game_id, user_id)
        if not member:
            return False
        return member.get('is_eliminated', False)
    
    def get_active_members(self, game_id: str) -> List[Dict[str, Any]]:
        """Get all active (non-eliminated) members of a game.
        
        Args:
            game_id: Game ID
            
        Returns:
            List of active member items
        """
        members = self.get_members(game_id)
        return [m for m in members if not m.get('is_eliminated', False)]
    
    def get_eliminated_members(self, game_id: str) -> List[Dict[str, Any]]:
        """Get all eliminated members of a game.
        
        Args:
            game_id: Game ID
            
        Returns:
            List of eliminated member items
        """
        members = self.get_members(game_id)
        return [m for m in members if m.get('is_eliminated', False)]
    
    def update_lives_remaining(self, game_id: str, user_id: str, lives: int) -> Dict[str, Any]:
        """Update lives remaining for a member (Last Man Standing).
        
        Args:
            game_id: Game ID
            user_id: User ID
            lives: Number of lives remaining
            
        Returns:
            Updated member item
        """
        return self.update_member(game_id, user_id, {'lives_remaining': lives})
