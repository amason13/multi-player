"""Round repository for DynamoDB operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from aws_lambda_powertools import Logger
from .table import DynamoDBTable
from ..utils.exceptions import NotFoundError, ValidationError

logger = Logger()


class RoundRepository:
    """Repository for round-related DynamoDB operations.
    
    Handles all round operations including creation, retrieval, match management,
    and prediction associations. Uses single-table design with item collections.
    
    Access Patterns:
    - Pattern #11: Create round
    - Pattern #12: Get round details
    - Pattern #10: Get game's rounds
    - Pattern #15: Get all predictions for round
    """
    
    def __init__(self, table: Optional[DynamoDBTable] = None):
        """Initialize round repository.
        
        Args:
            table: DynamoDBTable instance (creates new if not provided)
        """
        self.table = table or DynamoDBTable()
    
    # Round Metadata Operations
    
    def create_round(self, round_id: str, league_id: str, game_id: str,
                    round_number: int, game_type: str, **kwargs) -> Dict[str, Any]:
        """Create a new round.
        
        Args:
            round_id: Unique round identifier (UUID)
            league_id: Parent league ID
            game_id: Parent game ID
            round_number: Sequential round number
            game_type: Game type (POINTS_BASED, LAST_MAN_STANDING)
            **kwargs: Additional attributes (dates, status, etc.)
            
        Returns:
            Created round item
            
        Raises:
            ValidationError: If required fields are missing or invalid
        """
        if not round_id or not league_id or not game_id or round_number < 1:
            raise ValidationError("round_id, league_id, game_id, and round_number are required")
        
        now = datetime.utcnow().isoformat()
        
        item = {
            'PK': f'LEAGUE#{league_id}',
            'SK': f'ROUND#{round_number}',
            'entity_type': 'ROUND',
            'round_id': round_id,
            'league_id': league_id,
            'game_id': game_id,
            'round_number': round_number,
            'game_type': game_type,
            'status': 'SCHEDULED',
            'match_count': 0,
            'prediction_count': 0,
            'created_at': now,
            'updated_at': now,
            **kwargs
        }
        
        self.table.put_item(item)
        logger.info(f"Created round {round_number} in game {game_id}")
        return item
    
    def get_round(self, league_id: str, round_number: int) -> Optional[Dict[str, Any]]:
        """Get round details by league and round number.
        
        Args:
            league_id: League ID
            round_number: Round number
            
        Returns:
            Round metadata item or None if not found
        """
        return self.table.get_item(f'LEAGUE#{league_id}', f'ROUND#{round_number}')
    
    def get_round_by_id(self, round_id: str) -> Optional[Dict[str, Any]]:
        """Get round details by round ID.
        
        Note: This requires a scan or GSI lookup since round_id is not in primary key.
        For better performance, use get_round() with league_id and round_number.
        
        Args:
            round_id: Round ID
            
        Returns:
            Round metadata item or None if not found
        """
        # This would require a GSI or scan - not optimal
        # Prefer get_round(league_id, round_number) instead
        logger.warning("get_round_by_id requires scan - prefer get_round(league_id, round_number)")
        return None
    
    def update_round(self, league_id: str, round_number: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update round metadata.
        
        Args:
            league_id: League ID
            round_number: Round number
            updates: Dictionary of attributes to update
            
        Returns:
            Updated round item
        """
        updates['updated_at'] = datetime.utcnow().isoformat()
        result = self.table.update_item(
            f'LEAGUE#{league_id}',
            f'ROUND#{round_number}',
            updates
        )
        logger.info(f"Updated round {round_number} in league {league_id}")
        return result
    
    def delete_round(self, league_id: str, round_number: int) -> None:
        """Delete a round (soft delete - mark as cancelled).
        
        Args:
            league_id: League ID
            round_number: Round number
        """
        self.update_round(league_id, round_number, {'status': 'CANCELLED'})
        logger.info(f"Deleted round {round_number} in league {league_id}")
    
    # Match Operations
    
    def add_match(self, league_id: str, round_number: int, match_id: str,
                 home_team: str, away_team: str, **kwargs) -> Dict[str, Any]:
        """Add a match to a round.
        
        Args:
            league_id: League ID
            round_number: Round number
            match_id: Match ID
            home_team: Home team name
            away_team: Away team name
            **kwargs: Additional attributes (date, venue, etc.)
            
        Returns:
            Created match item
        """
        now = datetime.utcnow().isoformat()
        
        item = {
            'PK': f'LEAGUE#{league_id}',
            'SK': f'ROUND#{round_number}#MATCH#{match_id}',
            'entity_type': 'ROUND_MATCH',
            'match_id': match_id,
            'league_id': league_id,
            'round_number': round_number,
            'home_team': home_team,
            'away_team': away_team,
            'match_status': 'SCHEDULED',
            'prediction_count': 0,
            'created_at': now,
            'updated_at': now,
            **kwargs
        }
        
        self.table.put_item(item)
        
        # Update round match count
        round_item = self.get_round(league_id, round_number)
        if round_item:
            new_count = round_item.get('match_count', 0) + 1
            self.update_round(league_id, round_number, {'match_count': new_count})
        
        logger.info(f"Added match {match_id} to round {round_number}")
        return item
    
    def get_matches(self, league_id: str, round_number: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all matches in a round.
        
        Args:
            league_id: League ID
            round_number: Round number
            limit: Maximum number of matches to return
            
        Returns:
            List of match items
        """
        items = self.table.query(f'LEAGUE#{league_id}', f'ROUND#{round_number}#MATCH#')
        return items[:limit] if limit else items
    
    def get_match(self, league_id: str, round_number: int, match_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific match.
        
        Args:
            league_id: League ID
            round_number: Round number
            match_id: Match ID
            
        Returns:
            Match item or None if not found
        """
        return self.table.get_item(f'LEAGUE#{league_id}', f'ROUND#{round_number}#MATCH#{match_id}')
    
    def update_match(self, league_id: str, round_number: int, match_id: str,
                    updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update match details.
        
        Args:
            league_id: League ID
            round_number: Round number
            match_id: Match ID
            updates: Dictionary of attributes to update
            
        Returns:
            Updated match item
        """
        updates['updated_at'] = datetime.utcnow().isoformat()
        result = self.table.update_item(
            f'LEAGUE#{league_id}',
            f'ROUND#{round_number}#MATCH#{match_id}',
            updates
        )
        logger.info(f"Updated match {match_id} in round {round_number}")
        return result
    
    def remove_match(self, league_id: str, round_number: int, match_id: str) -> None:
        """Remove a match from a round.
        
        Args:
            league_id: League ID
            round_number: Round number
            match_id: Match ID
        """
        self.table.delete_item(f'LEAGUE#{league_id}', f'ROUND#{round_number}#MATCH#{match_id}')
        
        # Update round match count
        round_item = self.get_round(league_id, round_number)
        if round_item:
            new_count = max(0, round_item.get('match_count', 1) - 1)
            self.update_round(league_id, round_number, {'match_count': new_count})
        
        logger.info(f"Removed match {match_id} from round {round_number}")
    
    # Match Result Operations
    
    def set_match_result(self, league_id: str, round_number: int, match_id: str,
                        home_score: int, away_score: int) -> Dict[str, Any]:
        """Set the result of a match.
        
        Args:
            league_id: League ID
            round_number: Round number
            match_id: Match ID
            home_score: Home team score
            away_score: Away team score
            
        Returns:
            Updated match item
        """
        # Determine result
        if home_score > away_score:
            result = 'HOME_WIN'
        elif away_score > home_score:
            result = 'AWAY_WIN'
        else:
            result = 'DRAW'
        
        return self.update_match(
            league_id,
            round_number,
            match_id,
            {
                'home_score': home_score,
                'away_score': away_score,
                'result': result,
                'match_status': 'COMPLETED'
            }
        )
    
    # Round Status Operations
    
    def update_round_status(self, league_id: str, round_number: int, status: str) -> Dict[str, Any]:
        """Update round status.
        
        Args:
            league_id: League ID
            round_number: Round number
            status: New status (SCHEDULED, ACTIVE, LOCKED, COMPLETED, CANCELLED)
            
        Returns:
            Updated round item
        """
        valid_statuses = ['SCHEDULED', 'ACTIVE', 'LOCKED', 'COMPLETED', 'CANCELLED']
        if status not in valid_statuses:
            raise ValidationError(f"Invalid status: {status}")
        
        return self.update_round(league_id, round_number, {'status': status})
    
    def get_rounds_by_league(self, league_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all rounds in a league.
        
        Args:
            league_id: League ID
            limit: Maximum number of rounds to return
            
        Returns:
            List of round items (includes matches)
        """
        items = self.table.query(f'LEAGUE#{league_id}', 'ROUND#')
        # Filter to only round metadata items (not matches)
        rounds = [item for item in items if item.get('SK', '').count('#') == 1]
        return rounds[:limit] if limit else rounds
    
    def get_active_rounds(self, league_id: str) -> List[Dict[str, Any]]:
        """Get all active rounds in a league.
        
        Args:
            league_id: League ID
            
        Returns:
            List of active round items
        """
        rounds = self.get_rounds_by_league(league_id)
        return [r for r in rounds if r.get('status') == 'ACTIVE']
    
    def get_locked_rounds(self, league_id: str) -> List[Dict[str, Any]]:
        """Get all locked rounds in a league.
        
        Args:
            league_id: League ID
            
        Returns:
            List of locked round items
        """
        rounds = self.get_rounds_by_league(league_id)
        return [r for r in rounds if r.get('status') == 'LOCKED']
    
    def get_completed_rounds(self, league_id: str) -> List[Dict[str, Any]]:
        """Get all completed rounds in a league.
        
        Args:
            league_id: League ID
            
        Returns:
            List of completed round items
        """
        rounds = self.get_rounds_by_league(league_id)
        return [r for r in rounds if r.get('status') == 'COMPLETED']
