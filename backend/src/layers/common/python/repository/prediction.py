"""Prediction repository for DynamoDB operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from aws_lambda_powertools import Logger
from .table import DynamoDBTable
from ..utils.exceptions import NotFoundError, ValidationError

logger = Logger()


class PredictionRepository:
    """Repository for prediction-related DynamoDB operations.
    
    Handles all prediction operations including creation, retrieval, scoring,
    and user prediction history. Uses single-table design with item collections.
    
    Access Patterns:
    - Pattern #13: Submit prediction
    - Pattern #14: Get user's predictions for round
    - Pattern #15: Get all predictions for round
    - Pattern #19: Get user's pick history (LMS)
    """
    
    def __init__(self, table: Optional[DynamoDBTable] = None):
        """Initialize prediction repository.
        
        Args:
            table: DynamoDBTable instance (creates new if not provided)
        """
        self.table = table or DynamoDBTable()
    
    # Prediction CRUD Operations
    
    def create_prediction(self, prediction_id: str, user_id: str, league_id: str,
                         round_number: int, match_id: str, game_type: str,
                         **kwargs) -> Dict[str, Any]:
        """Create a new prediction.
        
        Args:
            prediction_id: Unique prediction identifier (UUID)
            user_id: User making the prediction
            league_id: League context
            round_number: Round number
            match_id: Match being predicted
            game_type: Game type (POINTS_BASED, LAST_MAN_STANDING)
            **kwargs: Additional attributes (scores, winner, confidence, etc.)
            
        Returns:
            Created prediction item
            
        Raises:
            ValidationError: If required fields are missing or invalid
        """
        if not all([prediction_id, user_id, league_id, round_number, match_id, game_type]):
            raise ValidationError("All required fields must be provided")
        
        now = datetime.utcnow().isoformat()
        
        item = {
            'PK': f'USER#{user_id}',
            'SK': f'PREDICTION#{league_id}#{round_number}#{match_id}',
            'entity_type': 'PREDICTION',
            'prediction_id': prediction_id,
            'user_id': user_id,
            'league_id': league_id,
            'round_number': round_number,
            'match_id': match_id,
            'game_type': game_type,
            'status': 'PENDING',
            'created_at': now,
            'updated_at': now,
            **kwargs
        }
        
        self.table.put_item(item)
        logger.info(f"Created prediction {prediction_id} for user {user_id}")
        return item
    
    def get_prediction(self, user_id: str, league_id: str, round_number: int,
                      match_id: str) -> Optional[Dict[str, Any]]:
        """Get a user's prediction for a specific match.
        
        Args:
            user_id: User ID
            league_id: League ID
            round_number: Round number
            match_id: Match ID
            
        Returns:
            Prediction item or None if not found
        """
        return self.table.get_item(
            f'USER#{user_id}',
            f'PREDICTION#{league_id}#{round_number}#{match_id}'
        )
    
    def update_prediction(self, user_id: str, league_id: str, round_number: int,
                         match_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a prediction.
        
        Args:
            user_id: User ID
            league_id: League ID
            round_number: Round number
            match_id: Match ID
            updates: Dictionary of attributes to update
            
        Returns:
            Updated prediction item
        """
        updates['updated_at'] = datetime.utcnow().isoformat()
        result = self.table.update_item(
            f'USER#{user_id}',
            f'PREDICTION#{league_id}#{round_number}#{match_id}',
            updates
        )
        logger.info(f"Updated prediction for user {user_id}")
        return result
    
    def delete_prediction(self, user_id: str, league_id: str, round_number: int,
                         match_id: str) -> None:
        """Delete a prediction (soft delete - mark as cancelled).
        
        Args:
            user_id: User ID
            league_id: League ID
            round_number: Round number
            match_id: Match ID
        """
        self.update_prediction(
            user_id,
            league_id,
            round_number,
            match_id,
            {'status': 'CANCELLED'}
        )
        logger.info(f"Deleted prediction for user {user_id}")
    
    # Prediction Submission Operations
    
    def submit_points_based_prediction(self, prediction_id: str, user_id: str,
                                      league_id: str, round_number: int, match_id: str,
                                      predicted_home_score: int, predicted_away_score: int,
                                      confidence_level: Optional[int] = None,
                                      reasoning: Optional[str] = None) -> Dict[str, Any]:
        """Submit a points-based prediction.
        
        Args:
            prediction_id: Unique prediction identifier
            user_id: User ID
            league_id: League ID
            round_number: Round number
            match_id: Match ID
            predicted_home_score: Predicted home team score
            predicted_away_score: Predicted away team score
            confidence_level: Confidence level (1-10)
            reasoning: User's reasoning
            
        Returns:
            Created prediction item
        """
        # Determine predicted result
        if predicted_home_score > predicted_away_score:
            predicted_result = 'HOME_WIN'
        elif predicted_away_score > predicted_home_score:
            predicted_result = 'AWAY_WIN'
        else:
            predicted_result = 'DRAW'
        
        return self.create_prediction(
            prediction_id=prediction_id,
            user_id=user_id,
            league_id=league_id,
            round_number=round_number,
            match_id=match_id,
            game_type='POINTS_BASED',
            predicted_home_score=predicted_home_score,
            predicted_away_score=predicted_away_score,
            predicted_result=predicted_result,
            confidence_level=confidence_level,
            reasoning=reasoning
        )
    
    def submit_lms_prediction(self, prediction_id: str, user_id: str,
                             league_id: str, round_number: int, match_id: str,
                             predicted_winner: str,
                             confidence_level: Optional[int] = None,
                             reasoning: Optional[str] = None) -> Dict[str, Any]:
        """Submit a Last Man Standing prediction.
        
        Args:
            prediction_id: Unique prediction identifier
            user_id: User ID
            league_id: League ID
            round_number: Round number
            match_id: Match ID
            predicted_winner: Predicted winner (HOME or AWAY)
            confidence_level: Confidence level (1-10)
            reasoning: User's reasoning
            
        Returns:
            Created prediction item
        """
        if predicted_winner not in ['HOME', 'AWAY']:
            raise ValidationError("predicted_winner must be HOME or AWAY")
        
        return self.create_prediction(
            prediction_id=prediction_id,
            user_id=user_id,
            league_id=league_id,
            round_number=round_number,
            match_id=match_id,
            game_type='LAST_MAN_STANDING',
            predicted_winner=predicted_winner,
            confidence_level=confidence_level,
            reasoning=reasoning
        )
    
    # Prediction Retrieval Operations
    
    def get_user_predictions_for_round(self, user_id: str, league_id: str,
                                      round_number: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all predictions for a user in a specific round.
        
        Args:
            user_id: User ID
            league_id: League ID
            round_number: Round number
            limit: Maximum number of predictions to return
            
        Returns:
            List of prediction items
        """
        items = self.table.query(
            f'USER#{user_id}',
            f'PREDICTION#{league_id}#{round_number}#'
        )
        return items[:limit] if limit else items
    
    def get_user_predictions_for_league(self, user_id: str, league_id: str,
                                       limit: int = 100) -> List[Dict[str, Any]]:
        """Get all predictions for a user in a league.
        
        Args:
            user_id: User ID
            league_id: League ID
            limit: Maximum number of predictions to return
            
        Returns:
            List of prediction items
        """
        items = self.table.query(
            f'USER#{user_id}',
            f'PREDICTION#{league_id}#'
        )
        return items[:limit] if limit else items
    
    def get_match_predictions(self, match_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all predictions for a specific match.
        
        Args:
            match_id: Match ID
            limit: Maximum number of predictions to return
            
        Returns:
            List of prediction items
        """
        # This would require a GSI lookup (GSI2PK=MATCH#{match_id})
        # For now, return empty list - implement with GSI query
        logger.warning("get_match_predictions requires GSI - not implemented")
        return []
    
    # Prediction Scoring Operations
    
    def score_points_based_prediction(self, user_id: str, league_id: str,
                                     round_number: int, match_id: str,
                                     actual_home_score: int, actual_away_score: int,
                                     points_earned: int) -> Dict[str, Any]:
        """Score a points-based prediction.
        
        Args:
            user_id: User ID
            league_id: League ID
            round_number: Round number
            match_id: Match ID
            actual_home_score: Actual home team score
            actual_away_score: Actual away team score
            points_earned: Points earned for this prediction
            
        Returns:
            Updated prediction item
        """
        # Determine actual result
        if actual_home_score > actual_away_score:
            actual_result = 'HOME_WIN'
        elif actual_away_score > actual_home_score:
            actual_result = 'AWAY_WIN'
        else:
            actual_result = 'DRAW'
        
        # Get prediction to check accuracy
        prediction = self.get_prediction(user_id, league_id, round_number, match_id)
        if not prediction:
            raise NotFoundError(f"Prediction not found for user {user_id}")
        
        # Determine accuracy type
        predicted_result = prediction.get('predicted_result')
        predicted_home = prediction.get('predicted_home_score')
        predicted_away = prediction.get('predicted_away_score')
        
        if predicted_home == actual_home_score and predicted_away == actual_away_score:
            accuracy_type = 'EXACT_SCORE'
        elif predicted_result == actual_result:
            accuracy_type = 'CORRECT_RESULT'
        else:
            accuracy_type = 'INCORRECT'
        
        return self.update_prediction(
            user_id,
            league_id,
            round_number,
            match_id,
            {
                'status': 'SCORED',
                'actual_home_score': actual_home_score,
                'actual_away_score': actual_away_score,
                'actual_result': actual_result,
                'accuracy_type': accuracy_type,
                'points_earned': points_earned,
                'scored_at': datetime.utcnow().isoformat()
            }
        )
    
    def score_lms_prediction(self, user_id: str, league_id: str,
                            round_number: int, match_id: str,
                            actual_winner: str, is_correct: bool) -> Dict[str, Any]:
        """Score a Last Man Standing prediction.
        
        Args:
            user_id: User ID
            league_id: League ID
            round_number: Round number
            match_id: Match ID
            actual_winner: Actual winner (HOME or AWAY)
            is_correct: Whether prediction was correct
            
        Returns:
            Updated prediction item
        """
        return self.update_prediction(
            user_id,
            league_id,
            round_number,
            match_id,
            {
                'status': 'SCORED',
                'actual_winner': actual_winner,
                'is_correct': is_correct,
                'is_alive': is_correct,  # User stays alive if correct
                'scored_at': datetime.utcnow().isoformat()
            }
        )
    
    # Prediction Status Operations
    
    def lock_prediction(self, user_id: str, league_id: str, round_number: int,
                       match_id: str) -> Dict[str, Any]:
        """Lock a prediction (prevent further edits).
        
        Args:
            user_id: User ID
            league_id: League ID
            round_number: Round number
            match_id: Match ID
            
        Returns:
            Updated prediction item
        """
        return self.update_prediction(
            user_id,
            league_id,
            round_number,
            match_id,
            {
                'status': 'LOCKED',
                'locked_at': datetime.utcnow().isoformat()
            }
        )
    
    def get_pending_predictions(self, user_id: str, league_id: str) -> List[Dict[str, Any]]:
        """Get all pending predictions for a user in a league.
        
        Args:
            user_id: User ID
            league_id: League ID
            
        Returns:
            List of pending prediction items
        """
        predictions = self.get_user_predictions_for_league(user_id, league_id)
        return [p for p in predictions if p.get('status') == 'PENDING']
    
    def get_locked_predictions(self, user_id: str, league_id: str) -> List[Dict[str, Any]]:
        """Get all locked predictions for a user in a league.
        
        Args:
            user_id: User ID
            league_id: League ID
            
        Returns:
            List of locked prediction items
        """
        predictions = self.get_user_predictions_for_league(user_id, league_id)
        return [p for p in predictions if p.get('status') == 'LOCKED']
    
    def get_scored_predictions(self, user_id: str, league_id: str) -> List[Dict[str, Any]]:
        """Get all scored predictions for a user in a league.
        
        Args:
            user_id: User ID
            league_id: League ID
            
        Returns:
            List of scored prediction items
        """
        predictions = self.get_user_predictions_for_league(user_id, league_id)
        return [p for p in predictions if p.get('status') == 'SCORED']
    
    # Prediction History Operations
    
    def get_pick_history(self, user_id: str, game_id: str) -> List[Dict[str, Any]]:
        """Get user's pick history for a game (Last Man Standing).
        
        Args:
            user_id: User ID
            game_id: Game ID
            
        Returns:
            List of predictions (picks) for the game
        """
        # This would require a GSI lookup (GSI8PK=USER#{user_id}#GAME#{game_id})
        # For now, return empty list - implement with GSI query
        logger.warning("get_pick_history requires GSI - not implemented")
        return []
    
    def has_picked_team(self, user_id: str, game_id: str, round_number: int,
                       team_id: str) -> bool:
        """Check if user has already picked a team in a game (LMS duplicate prevention).
        
        Args:
            user_id: User ID
            game_id: Game ID
            round_number: Round number
            team_id: Team ID
            
        Returns:
            True if team has been picked, False otherwise
        """
        # This would require checking pick history
        # For now, return False - implement with GSI query
        logger.warning("has_picked_team requires GSI - not implemented")
        return False
