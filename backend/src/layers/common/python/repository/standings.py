"""Standings repository for DynamoDB operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from aws_lambda_powertools import Logger
from .table import DynamoDBTable
from ..utils.exceptions import NotFoundError, ValidationError

logger = Logger()


class StandingsRepository:
    """Repository for standings-related DynamoDB operations.
    
    Handles all standings operations including creation, retrieval, computation,
    and ranking management. Uses single-table design with item collections.
    
    Access Patterns:
    - Pattern #16: Get game standings
    - Pattern #17: Get league standings
    - Pattern #18: Get user's stats in league
    """
    
    def __init__(self, table: Optional[DynamoDBTable] = None):
        """Initialize standings repository.
        
        Args:
            table: DynamoDBTable instance (creates new if not provided)
        """
        self.table = table or DynamoDBTable()
    
    # Standings CRUD Operations
    
    def create_standings(self, standings_id: str, league_id: str, game_id: str,
                        game_type: str, round_number: int,
                        standings_data: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Create standings for a league/game round.
        
        Args:
            standings_id: Unique standings identifier (UUID)
            league_id: League ID
            game_id: Game ID
            game_type: Game type (POINTS_BASED, LAST_MAN_STANDING)
            round_number: Round number (0 for final)
            standings_data: Array of player standings entries
            **kwargs: Additional attributes (title, description, etc.)
            
        Returns:
            Created standings item
            
        Raises:
            ValidationError: If required fields are missing or invalid
        """
        if not all([standings_id, league_id, game_id, game_type]):
            raise ValidationError("All required fields must be provided")
        
        now = datetime.utcnow().isoformat()
        
        # Calculate participant counts
        total_participants = len(standings_data)
        active_participants = sum(1 for entry in standings_data if entry.get('is_alive', True))
        eliminated_participants = total_participants - active_participants
        
        item = {
            'PK': f'LEAGUE#{league_id}',
            'SK': f'STANDINGS#{game_type}#{round_number}' if round_number > 0 else f'STANDINGS#{game_type}#FINAL',
            'entity_type': 'STANDINGS',
            'standings_id': standings_id,
            'league_id': league_id,
            'game_id': game_id,
            'game_type': game_type,
            'round_number': round_number,
            'is_final': round_number == 0,
            'total_participants': total_participants,
            'active_participants': active_participants,
            'eliminated_participants': eliminated_participants,
            'standings_data': standings_data,
            'created_at': now,
            'updated_at': now,
            'computed_at': now,
            **kwargs
        }
        
        self.table.put_item(item)
        logger.info(f"Created standings for league {league_id}, game {game_id}, round {round_number}")
        return item
    
    def get_standings(self, league_id: str, game_type: str, round_number: int) -> Optional[Dict[str, Any]]:
        """Get standings for a league/game round.
        
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
    
    def update_standings(self, league_id: str, game_type: str, round_number: int,
                        updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update standings.
        
        Args:
            league_id: League ID
            game_type: Game type
            round_number: Round number
            updates: Dictionary of attributes to update
            
        Returns:
            Updated standings item
        """
        updates['updated_at'] = datetime.utcnow().isoformat()
        result = self.table.update_item(
            f'LEAGUE#{league_id}',
            f'STANDINGS#{game_type}#{round_number}',
            updates
        )
        logger.info(f"Updated standings for league {league_id}, round {round_number}")
        return result
    
    def delete_standings(self, league_id: str, game_type: str, round_number: int) -> None:
        """Delete standings (soft delete - mark as archived).
        
        Args:
            league_id: League ID
            game_type: Game type
            round_number: Round number
        """
        self.table.delete_item(
            f'LEAGUE#{league_id}',
            f'STANDINGS#{game_type}#{round_number}'
        )
        logger.info(f"Deleted standings for league {league_id}, round {round_number}")
    
    # Standings Retrieval Operations
    
    def get_user_standing(self, league_id: str, game_type: str, round_number: int,
                         user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific user's standing in a round.
        
        Args:
            league_id: League ID
            game_type: Game type
            round_number: Round number
            user_id: User ID
            
        Returns:
            User's standing entry or None if not found
        """
        standings = self.get_standings(league_id, game_type, round_number)
        if not standings:
            return None
        
        standings_data = standings.get('standings_data', [])
        for entry in standings_data:
            if entry.get('user_id') == user_id:
                return entry
        
        return None
    
    def get_top_players(self, league_id: str, game_type: str, round_number: int,
                       limit: int = 10) -> List[Dict[str, Any]]:
        """Get top players in standings.
        
        Args:
            league_id: League ID
            game_type: Game type
            round_number: Round number
            limit: Number of top players to return
            
        Returns:
            List of top player standings entries
        """
        standings = self.get_standings(league_id, game_type, round_number)
        if not standings:
            return []
        
        standings_data = standings.get('standings_data', [])
        return standings_data[:limit]
    
    def get_user_rank(self, league_id: str, game_type: str, round_number: int,
                     user_id: str) -> Optional[int]:
        """Get a user's rank in standings.
        
        Args:
            league_id: League ID
            game_type: Game type
            round_number: Round number
            user_id: User ID
            
        Returns:
            User's rank or None if not found
        """
        standing = self.get_user_standing(league_id, game_type, round_number, user_id)
        if standing:
            return standing.get('rank')
        return None
    
    # Standings Computation Operations
    
    def compute_points_based_standings(self, league_id: str, game_id: str,
                                      round_number: int, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute standings from points-based predictions.
        
        Args:
            league_id: League ID
            game_id: Game ID
            round_number: Round number
            predictions: List of scored predictions
            
        Returns:
            Computed standings item
        """
        # Group predictions by user
        user_stats = {}
        for pred in predictions:
            user_id = pred.get('user_id')
            if user_id not in user_stats:
                user_stats[user_id] = {
                    'user_id': user_id,
                    'user_name': pred.get('user_name', 'Unknown'),
                    'avatar_url': pred.get('avatar_url'),
                    'total_points': 0,
                    'round_points': 0,
                    'games_played': 1,
                    'correct_predictions': 0,
                    'total_predictions': 0,
                    'highest_score': 0,
                    'lowest_score': float('inf')
                }
            
            points = pred.get('points_earned', 0)
            user_stats[user_id]['total_points'] += points
            user_stats[user_id]['round_points'] += points
            user_stats[user_id]['total_predictions'] += 1
            
            if pred.get('accuracy_type') == 'EXACT_SCORE':
                user_stats[user_id]['correct_predictions'] += 1
            elif pred.get('accuracy_type') == 'CORRECT_RESULT':
                user_stats[user_id]['correct_predictions'] += 1
            
            user_stats[user_id]['highest_score'] = max(
                user_stats[user_id]['highest_score'],
                points
            )
            user_stats[user_id]['lowest_score'] = min(
                user_stats[user_id]['lowest_score'],
                points
            )
        
        # Sort by total points
        sorted_users = sorted(
            user_stats.values(),
            key=lambda x: x['total_points'],
            reverse=True
        )
        
        # Assign ranks
        standings_data = []
        for rank, user_stat in enumerate(sorted_users, 1):
            user_stat['rank'] = rank
            user_stat['previous_rank'] = 0  # Would need to fetch from previous round
            user_stat['rank_change'] = 0
            user_stat['average_points_per_game'] = user_stat['total_points'] / user_stat['games_played']
            user_stat['prediction_accuracy'] = (
                (user_stat['correct_predictions'] / user_stat['total_predictions'] * 100)
                if user_stat['total_predictions'] > 0 else 0
            )
            standings_data.append(user_stat)
        
        return self.create_standings(
            standings_id=f'standings-{league_id}-{round_number}',
            league_id=league_id,
            game_id=game_id,
            game_type='POINTS_BASED',
            round_number=round_number,
            standings_data=standings_data
        )
    
    def compute_lms_standings(self, league_id: str, game_id: str,
                             round_number: int, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute standings from Last Man Standing predictions.
        
        Args:
            league_id: League ID
            game_id: Game ID
            round_number: Round number
            predictions: List of scored predictions
            
        Returns:
            Computed standings item
        """
        # Group predictions by user
        user_stats = {}
        for pred in predictions:
            user_id = pred.get('user_id')
            if user_id not in user_stats:
                user_stats[user_id] = {
                    'user_id': user_id,
                    'user_name': pred.get('user_name', 'Unknown'),
                    'avatar_url': pred.get('avatar_url'),
                    'is_alive': True,
                    'games_won': 0,
                    'games_lost': 0,
                    'consecutive_wins': 0,
                    'consecutive_losses': 0,
                    'best_consecutive_wins': 0,
                    'lives_remaining': 3,
                    'eliminated_round': None
                }
            
            if pred.get('is_correct'):
                user_stats[user_id]['games_won'] += 1
                user_stats[user_id]['consecutive_wins'] += 1
                user_stats[user_id]['consecutive_losses'] = 0
                user_stats[user_id]['best_consecutive_wins'] = max(
                    user_stats[user_id]['best_consecutive_wins'],
                    user_stats[user_id]['consecutive_wins']
                )
            else:
                user_stats[user_id]['games_lost'] += 1
                user_stats[user_id]['consecutive_losses'] += 1
                user_stats[user_id]['consecutive_wins'] = 0
                user_stats[user_id]['is_alive'] = False
                user_stats[user_id]['eliminated_round'] = round_number
        
        # Sort by games_won
        sorted_users = sorted(
            user_stats.values(),
            key=lambda x: (x['games_won'], x['best_consecutive_wins']),
            reverse=True
        )
        
        # Assign ranks
        standings_data = []
        for rank, user_stat in enumerate(sorted_users, 1):
            user_stat['rank'] = rank
            user_stat['previous_rank'] = 0
            user_stat['rank_change'] = 0
            total_games = user_stat['games_won'] + user_stat['games_lost']
            user_stat['win_percentage'] = (
                (user_stat['games_won'] / total_games * 100)
                if total_games > 0 else 0
            )
            standings_data.append(user_stat)
        
        return self.create_standings(
            standings_id=f'standings-{league_id}-{round_number}',
            league_id=league_id,
            game_id=game_id,
            game_type='LAST_MAN_STANDING',
            round_number=round_number,
            standings_data=standings_data
        )
    
    # Standings Management Operations
    
    def lock_standings(self, league_id: str, game_type: str, round_number: int,
                      locked_by: str) -> Dict[str, Any]:
        """Lock standings (prevent further updates).
        
        Args:
            league_id: League ID
            game_type: Game type
            round_number: Round number
            locked_by: User ID who locked standings
            
        Returns:
            Updated standings item
        """
        return self.update_standings(
            league_id,
            game_type,
            round_number,
            {
                'is_locked': True,
                'locked_at': datetime.utcnow().isoformat(),
                'locked_by': locked_by
            }
        )
    
    def archive_standings(self, league_id: str, game_type: str, round_number: int) -> None:
        """Archive standings (mark as read-only).
        
        Args:
            league_id: League ID
            game_type: Game type
            round_number: Round number
        """
        self.update_standings(
            league_id,
            game_type,
            round_number,
            {'status': 'ARCHIVED'}
        )
        logger.info(f"Archived standings for league {league_id}, round {round_number}")
