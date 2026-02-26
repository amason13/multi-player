"""Get standings Lambda function - Patterns #16-17."""
import json
import os
from typing import Optional, List, Dict, Any

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from pydantic import BaseModel, Field

from common.repository.standings import StandingsRepository
from common.repository.league import LeagueRepository
from common.utils.responses import success_response, error_response
from common.utils.exceptions import NotFoundError, UnauthorizedError, ValidationError, MultiPlayerException

logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Initialize repositories
standings_repo = StandingsRepository()
league_repo = LeagueRepository()


class StandingEntry(BaseModel):
    """Individual standing entry."""
    
    rank: int
    user_id: str
    user_name: Optional[str] = None
    avatar_url: Optional[str] = None
    total_points: Optional[int] = None
    games_played: Optional[int] = None
    average_points_per_game: Optional[float] = None
    prediction_accuracy: Optional[float] = None
    games_won: Optional[int] = None
    games_lost: Optional[int] = None
    win_percentage: Optional[float] = None
    is_alive: Optional[bool] = None
    eliminated_round: Optional[int] = None


class GetStandingsResponse(BaseModel):
    """Response model for get standings."""
    
    league_id: str
    game_type: str
    round_number: int
    is_final: bool
    total_participants: int
    active_participants: int
    standings: List[StandingEntry]


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Get standings for a league or game.
    
    Access Patterns #16-17: Get game/league standings
    
    This handler retrieves standings for a specific league and round.
    Supports both points-based and Last Man Standing game types.
    
    The user must be authenticated and a member of the league.
    
    Path Parameters:
        leagueId: The ID of the league
    
    Query Parameters:
        gameType (optional): Game type (POINTS_BASED or LAST_MAN_STANDING)
        roundNumber (optional): Round number (default: latest round)
        isFinal (optional): Get final standings (true/false)
    
    Args:
        event: API Gateway Lambda proxy integration event
        context: Lambda context object
    
    Returns:
        API Gateway response with standings data or error
        
    Raises:
        UnauthorizedError: If user is not authenticated
        NotFoundError: If league or standings not found
        ValidationError: If input validation fails
        MultiPlayerException: For other application errors
    
    Example:
        GET /leagues/{leagueId}/standings?gameType=POINTS_BASED&roundNumber=1
        
        Response (200):
        {
            "league_id": "league-uuid",
            "game_type": "POINTS_BASED",
            "round_number": 1,
            "is_final": false,
            "total_participants": 12,
            "active_participants": 12,
            "standings": [
                {
                    "rank": 1,
                    "user_id": "user-uuid-1",
                    "user_name": "John Doe",
                    "avatar_url": "https://example.com/avatar.jpg",
                    "total_points": 145,
                    "games_played": 5,
                    "average_points_per_game": 29.0,
                    "prediction_accuracy": 85.5
                },
                {
                    "rank": 2,
                    "user_id": "user-uuid-2",
                    "user_name": "Jane Smith",
                    "avatar_url": "https://example.com/avatar2.jpg",
                    "total_points": 138,
                    "games_played": 5,
                    "average_points_per_game": 27.6,
                    "prediction_accuracy": 82.0
                }
            ]
        }
    """
    try:
        # Extract user ID from Cognito claims
        authorizer = event.get('requestContext', {}).get('authorizer', {})
        claims = authorizer.get('claims', {})
        user_id = claims.get('sub')
        
        if not user_id:
            logger.warning("Missing user ID in Cognito claims")
            raise UnauthorizedError("User not authenticated")
        
        # Extract league ID from path parameters
        path_params = event.get('pathParameters', {}) or {}
        league_id = path_params.get('leagueId')
        
        if not league_id:
            logger.warning("Missing league ID in path parameters")
            return error_response(
                message="League ID is required",
                status_code=400,
                error_code="MISSING_PARAMETER"
            )
        
        # Parse query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        game_type = query_params.get('gameType', 'POINTS_BASED')
        round_number = int(query_params.get('roundNumber', 1))
        is_final = query_params.get('isFinal', 'false').lower() == 'true'
        
        # Validate game type
        if game_type not in ['POINTS_BASED', 'LAST_MAN_STANDING']:
            raise ValidationError(f"Invalid game type: {game_type}")
        
        logger.info(
            f"Retrieving standings for league: {league_id}, "
            f"game_type: {game_type}, round: {round_number}, is_final: {is_final}"
        )
        metrics.add_metric(name="StandingsGetRequest", unit="Count", value=1)
        
        # Verify user is a member of the league
        is_member = league_repo.is_member(league_id, user_id)
        if not is_member:
            logger.warning(f"User {user_id} is not a member of league {league_id}")
            raise NotFoundError(f"League {league_id} not found or access denied")
        
        # Verify league exists
        league = league_repo.get_league(league_id)
        if not league:
            logger.warning(f"League not found: {league_id}")
            raise NotFoundError(f"League {league_id} not found")
        
        # Get standings
        if is_final:
            standings = standings_repo.get_final_standings(league_id, game_type)
        else:
            standings = standings_repo.get_standings(league_id, game_type, round_number)
        
        if not standings:
            logger.warning(
                f"Standings not found for league: {league_id}, "
                f"game_type: {game_type}, round: {round_number}"
            )
            raise NotFoundError(
                f"Standings not found for league {league_id} "
                f"(game_type: {game_type}, round: {round_number})"
            )
        
        # Build response
        standings_data = standings.get('standings_data', [])
        standing_entries = []
        
        for entry in standings_data:
            standing_entries.append({
                'rank': entry.get('rank'),
                'user_id': entry.get('user_id'),
                'user_name': entry.get('user_name'),
                'avatar_url': entry.get('avatar_url'),
                'total_points': entry.get('total_points'),
                'games_played': entry.get('games_played'),
                'average_points_per_game': entry.get('average_points_per_game'),
                'prediction_accuracy': entry.get('prediction_accuracy'),
                'games_won': entry.get('games_won'),
                'games_lost': entry.get('games_lost'),
                'win_percentage': entry.get('win_percentage'),
                'is_alive': entry.get('is_alive'),
                'eliminated_round': entry.get('eliminated_round')
            })
        
        response_data = {
            'league_id': standings.get('league_id'),
            'game_type': standings.get('game_type'),
            'round_number': standings.get('round_number', round_number),
            'is_final': standings.get('is_final', is_final),
            'total_participants': standings.get('total_participants', len(standing_entries)),
            'active_participants': standings.get('active_participants', len(standing_entries)),
            'standings': standing_entries
        }
        
        # Validate response
        validated_response = GetStandingsResponse(**response_data)
        
        logger.info(f"Retrieved standings for league: {league_id}")
        metrics.add_metric(name="StandingsRetrieved", unit="Count", value=1)
        
        return success_response(
            data=validated_response.dict(),
            status_code=200
        )
    
    except UnauthorizedError as e:
        logger.warning(f"Unauthorized: {e.message}")
        metrics.add_metric(name="StandingsGetUnauthorized", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except NotFoundError as e:
        logger.warning(f"Not found: {e.message}")
        metrics.add_metric(name="StandingsGetNotFound", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        metrics.add_metric(name="StandingsGetValidationError", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except MultiPlayerException as e:
        logger.warning(f"Application error: {e.message}")
        metrics.add_metric(name="StandingsGetError", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error retrieving standings: {str(e)}")
        metrics.add_metric(name="StandingsGetException", unit="Count", value=1)
        return error_response(
            message="Internal server error",
            status_code=500,
            error_code="INTERNAL_ERROR"
        )
