"""Score round batch operation Lambda function - Pattern #24."""
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
import boto3

logger = Logger()
tracer = Tracer()
metrics = Metrics()

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TABLE_NAME'))


def calculate_points_based_score(
    predicted_home: int,
    predicted_away: int,
    actual_home: int,
    actual_away: int,
    bonus_multiplier: float = 1.0
) -> tuple[int, str, Dict[str, int]]:
    """Calculate points for points-based prediction.
    
    Args:
        predicted_home: Predicted home team score
        predicted_away: Predicted away team score
        actual_home: Actual home team score
        actual_away: Actual away team score
        bonus_multiplier: Bonus points multiplier
    
    Returns:
        Tuple of (total_points, accuracy_type, points_breakdown)
    """
    base_points = 0
    points_breakdown = {'result': 0, 'score': 0}
    
    # Determine predicted and actual results
    if predicted_home > predicted_away:
        predicted_result = 'HOME_WIN'
    elif predicted_away > predicted_home:
        predicted_result = 'AWAY_WIN'
    else:
        predicted_result = 'DRAW'
    
    if actual_home > actual_away:
        actual_result = 'HOME_WIN'
    elif actual_away > actual_home:
        actual_result = 'AWAY_WIN'
    else:
        actual_result = 'DRAW'
    
    # Check for exact score match
    if predicted_home == actual_home and predicted_away == actual_away:
        base_points = 10
        points_breakdown['score'] = 10
        accuracy_type = 'EXACT_SCORE'
    # Check for correct result
    elif predicted_result == actual_result:
        base_points = 5
        points_breakdown['result'] = 5
        accuracy_type = 'CORRECT_RESULT'
    else:
        base_points = 0
        accuracy_type = 'INCORRECT'
    
    # Apply bonus multiplier
    total_points = int(base_points * bonus_multiplier)
    
    return total_points, accuracy_type, points_breakdown


def calculate_lms_score(
    predicted_winner: str,
    actual_winner: str
) -> tuple[bool, str]:
    """Calculate correctness for Last Man Standing prediction.
    
    Args:
        predicted_winner: Predicted winner (HOME or AWAY)
        actual_winner: Actual winner (HOME, AWAY, or DRAW)
    
    Returns:
        Tuple of (is_correct, accuracy_type)
    """
    if actual_winner == 'DRAW':
        return False, 'DRAW'
    
    is_correct = predicted_winner == actual_winner
    accuracy_type = 'CORRECT' if is_correct else 'INCORRECT'
    
    return is_correct, accuracy_type


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Score all completed rounds and update predictions and standings.
    
    Pattern #24: Score round (batch operation)
    
    This function is typically triggered by:
    - EventBridge scheduled rule (e.g., daily at 2 AM)
    - Manual invocation via API
    
    Expected event:
    {
        "game_ids": ["game-uuid-1", "game-uuid-2"],  # Optional: specific games
        "league_ids": ["league-uuid-1"],  # Optional: specific leagues
        "round_numbers": [1, 2, 3],  # Optional: specific rounds
        "force_rescore": false  # Optional: rescore already scored rounds
    }
    
    Returns:
        API Gateway response with scoring results
    """
    try:
        logger.info("Starting round scoring batch operation")
        
        # Parse event parameters
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
        game_ids = body.get('game_ids', [])
        league_ids = body.get('league_ids', [])
        round_numbers = body.get('round_numbers', [])
        force_rescore = body.get('force_rescore', False)
        
        # Track scoring results
        scoring_results = {
            'rounds_scored': 0,
            'predictions_scored': 0,
            'standings_updated': 0,
            'errors': []
        }
        
        # Get all rounds to score
        rounds_to_score = _get_rounds_to_score(game_ids, league_ids, round_numbers, force_rescore)
        logger.info(f"Found {len(rounds_to_score)} rounds to score")
        
        # Score each round
        for round_item in rounds_to_score:
            try:
                result = _score_round(round_item)
                scoring_results['rounds_scored'] += 1
                scoring_results['predictions_scored'] += result['predictions_scored']
                scoring_results['standings_updated'] += result['standings_updated']
                
                logger.info(
                    f"Scored round {round_item['round_number']} in game {round_item['game_id']}: "
                    f"{result['predictions_scored']} predictions, "
                    f"{result['standings_updated']} standings updated"
                )
            except Exception as e:
                error_msg = f"Error scoring round {round_item.get('round_number')}: {str(e)}"
                logger.exception(error_msg)
                scoring_results['errors'].append(error_msg)
        
        # Log metrics
        metrics.add_metric(name="RoundsScored", unit="Count", value=scoring_results['rounds_scored'])
        metrics.add_metric(name="PredictionsScored", unit="Count", value=scoring_results['predictions_scored'])
        metrics.add_metric(name="StandingsUpdated", unit="Count", value=scoring_results['standings_updated'])
        
        logger.info(f"Scoring batch complete: {scoring_results}")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Round scoring completed',
                'results': scoring_results
            })
        }
    
    except Exception as e:
        logger.exception(f"Error in scoring batch operation: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error during scoring',
                'errorCode': 'SCORING_ERROR'
            })
        }


def _get_rounds_to_score(
    game_ids: List[str],
    league_ids: List[str],
    round_numbers: List[int],
    force_rescore: bool
) -> List[Dict[str, Any]]:
    """Get all rounds that need scoring.
    
    Args:
        game_ids: Specific game IDs to score (empty = all)
        league_ids: Specific league IDs to score (empty = all)
        round_numbers: Specific round numbers to score (empty = all)
        force_rescore: Whether to rescore already scored rounds
    
    Returns:
        List of round items to score
    """
    rounds_to_score = []
    
    # If specific games provided, query those
    if game_ids:
        for game_id in game_ids:
            items = table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                ExpressionAttributeValues={
                    ':pk': f'GAME#{game_id}',
                    ':sk': 'ROUND#'
                }
            )
            rounds_to_score.extend(items.get('Items', []))
    
    # If specific leagues provided, query those
    elif league_ids:
        for league_id in league_ids:
            items = table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                ExpressionAttributeValues={
                    ':pk': f'LEAGUE#{league_id}',
                    ':sk': 'ROUND#'
                }
            )
            rounds_to_score.extend(items.get('Items', []))
    
    # Filter by round numbers if specified
    if round_numbers:
        rounds_to_score = [r for r in rounds_to_score if r.get('round_number') in round_numbers]
    
    # Filter by status (only score LOCKED or COMPLETED rounds, unless force_rescore)
    if not force_rescore:
        rounds_to_score = [
            r for r in rounds_to_score
            if r.get('status') in ['LOCKED', 'COMPLETED']
        ]
    
    return rounds_to_score


def _score_round(round_item: Dict[str, Any]) -> Dict[str, int]:
    """Score all predictions for a round.
    
    Args:
        round_item: Round metadata item
    
    Returns:
        Dictionary with scoring results
    """
    game_id = round_item['game_id']
    league_id = round_item['league_id']
    round_number = round_item['round_number']
    round_id = round_item['round_id']
    
    results = {
        'predictions_scored': 0,
        'standings_updated': 0
    }
    
    # Get all matches for this round
    matches = table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
        ExpressionAttributeValues={
            ':pk': f'GAME#{game_id}',
            ':sk': f'ROUND#{round_number}#MATCH#'
        }
    )
    
    matches_by_id = {m['match_id']: m for m in matches.get('Items', [])}
    
    # Get all predictions for this round
    predictions = table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
        ExpressionAttributeValues={
            ':pk': f'GAME#{game_id}',
            ':sk': f'ROUND#{round_number}#PREDICTION#'
        }
    )
    
    # Score each prediction
    now = datetime.utcnow().isoformat()
    user_points = {}  # Track points per user for standings
    
    for prediction in predictions.get('Items', []):
        match_id = prediction.get('match_id')
        user_id = prediction.get('user_id')
        match = matches_by_id.get(match_id)
        
        if not match or match.get('match_status') != 'COMPLETED':
            continue
        
        # Skip if already scored
        if prediction.get('status') == 'SCORED':
            continue
        
        # Calculate points based on game type
        game_type = round_item.get('game_type', 'POINTS_BASED')
        
        if game_type == 'POINTS_BASED':
            points, accuracy_type, breakdown = calculate_points_based_score(
                prediction.get('predicted_home_score', 0),
                prediction.get('predicted_away_score', 0),
                match.get('home_score', 0),
                match.get('away_score', 0),
                match.get('bonus_multiplier', 1.0)
            )
            
            # Update prediction
            table.update_item(
                f'GAME#{game_id}',
                f'ROUND#{round_number}#PREDICTION#{user_id}#{match_id}',
                {
                    'status': 'SCORED',
                    'points_earned': points,
                    'accuracy_type': accuracy_type,
                    'points_breakdown': breakdown,
                    'actual_home_score': match.get('home_score'),
                    'actual_away_score': match.get('away_score'),
                    'actual_result': match.get('result'),
                    'scored_at': now,
                    'updated_at': now
                }
            )
        
        elif game_type == 'LAST_MAN_STANDING':
            is_correct, accuracy_type = calculate_lms_score(
                prediction.get('predicted_winner', ''),
                match.get('result', 'DRAW')
            )
            
            # Update prediction
            table.update_item(
                f'GAME#{game_id}',
                f'ROUND#{round_number}#PREDICTION#{user_id}#{match_id}',
                {
                    'status': 'SCORED',
                    'is_correct': is_correct,
                    'accuracy_type': accuracy_type,
                    'actual_winner': match.get('result'),
                    'scored_at': now,
                    'updated_at': now
                }
            )
            
            # Track for LMS elimination
            if not is_correct:
                # Mark user as eliminated in game
                _eliminate_user_from_game(game_id, user_id, round_number)
        
        # Track points for standings update
        if user_id not in user_points:
            user_points[user_id] = 0
        if game_type == 'POINTS_BASED':
            user_points[user_id] += points
        
        results['predictions_scored'] += 1
    
    # Update standings
    if user_points:
        _update_standings(game_id, league_id, round_number, user_points)
        results['standings_updated'] = 1
    
    # Mark round as completed
    table.update_item(
        f'GAME#{game_id}',
        f'ROUND#{round_number}',
        {
            'status': 'COMPLETED',
            'updated_at': now
        }
    )
    
    return results


def _eliminate_user_from_game(game_id: str, user_id: str, round_number: int) -> None:
    """Mark user as eliminated in LMS game.
    
    Args:
        game_id: Game ID
        user_id: User ID
        round_number: Round number where eliminated
    """
    now = datetime.utcnow().isoformat()
    
    # Update game member status
    table.update_item(
        f'GAME#{game_id}',
        f'MEMBER#{user_id}',
        {
            'is_alive': False,
            'eliminated_round': round_number,
            'eliminated_at': now,
            'updated_at': now
        }
    )
    
    logger.info(f"User {user_id} eliminated from game {game_id} in round {round_number}")


def _update_standings(
    game_id: str,
    league_id: str,
    round_number: int,
    user_points: Dict[str, int]
) -> None:
    """Update standings after round scoring.
    
    Args:
        game_id: Game ID
        league_id: League ID
        round_number: Round number
        user_points: Dictionary of user_id -> points earned
    """
    now = datetime.utcnow().isoformat()
    
    # Get current standings
    standings_key = f'STANDINGS#{game_id}#{round_number}'
    standings = table.get_item(
        Key={
            'PK': f'GAME#{game_id}',
            'SK': standings_key
        }
    )
    
    standings_item = standings.get('Item', {})
    standings_data = standings_item.get('standings_data', [])
    
    # Update user entries in standings
    for user_id, points in user_points.items():
        # Find or create user entry
        user_entry = next((e for e in standings_data if e['user_id'] == user_id), None)
        
        if user_entry:
            user_entry['round_points'] = points
            user_entry['total_points'] = user_entry.get('total_points', 0) + points
            user_entry['games_played'] = user_entry.get('games_played', 0) + 1
        else:
            user_entry = {
                'user_id': user_id,
                'rank': len(standings_data) + 1,
                'total_points': points,
                'round_points': points,
                'games_played': 1
            }
            standings_data.append(user_entry)
    
    # Re-sort standings by total points
    standings_data.sort(key=lambda x: x.get('total_points', 0), reverse=True)
    
    # Update ranks
    for idx, entry in enumerate(standings_data, 1):
        entry['rank'] = idx
    
    # Update standings item
    standings_item['standings_data'] = standings_data
    standings_item['updated_at'] = now
    
    table.put_item(standings_item)
    
    logger.info(f"Updated standings for game {game_id} round {round_number}")
