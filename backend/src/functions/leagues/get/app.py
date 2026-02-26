"""Get league details Lambda function - Pattern #4."""
import json
import os
from typing import Optional, List, Dict, Any

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from pydantic import BaseModel, Field

from common.repository.league import LeagueRepository
from common.utils.responses import success_response, error_response
from common.utils.exceptions import NotFoundError, UnauthorizedError, MultiPlayerException

logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Initialize repository
league_repo = LeagueRepository()


class LeagueDetail(BaseModel):
    """League detail response model."""
    
    league_id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    member_count: int
    game_count: int
    status: str
    created_at: str
    updated_at: str


class GetLeagueResponse(BaseModel):
    """Response model for get league."""
    
    league: LeagueDetail


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Get league details by ID.
    
    Access Pattern #4: Get league details
    
    This handler retrieves detailed information about a specific league.
    The user must be authenticated and a member of the league to access it.
    
    Path Parameters:
        leagueId: The ID of the league to retrieve
    
    Args:
        event: API Gateway Lambda proxy integration event
        context: Lambda context object
    
    Returns:
        API Gateway response with league details or error
        
    Raises:
        UnauthorizedError: If user is not authenticated
        NotFoundError: If league not found
        MultiPlayerException: For other application errors
    
    Example:
        GET /leagues/{leagueId}
        
        Response (200):
        {
            "league": {
                "league_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Premier League 2024",
                "description": "Fantasy football league",
                "owner_id": "550e8400-e29b-41d4-a716-446655440001",
                "member_count": 12,
                "game_count": 38,
                "status": "ACTIVE",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-20T14:45:00"
            }
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
        
        logger.info(f"Retrieving league: {league_id} for user: {user_id}")
        metrics.add_metric(name="LeagueGetRequest", unit="Count", value=1)
        
        # Verify user is a member of the league
        is_member = league_repo.is_member(league_id, user_id)
        if not is_member:
            logger.warning(f"User {user_id} is not a member of league {league_id}")
            raise NotFoundError(f"League {league_id} not found or access denied")
        
        # Get league details from repository
        league = league_repo.get_league(league_id)
        
        if not league:
            logger.warning(f"League not found: {league_id}")
            raise NotFoundError(f"League {league_id} not found")
        
        # Build response
        response_data = {
            'league': {
                'league_id': league.get('league_id'),
                'name': league.get('name'),
                'description': league.get('description'),
                'owner_id': league.get('owner_id'),
                'member_count': league.get('member_count', 0),
                'game_count': league.get('game_count', 0),
                'status': league.get('status', 'ACTIVE'),
                'created_at': league.get('created_at'),
                'updated_at': league.get('updated_at')
            }
        }
        
        # Validate response
        validated_response = GetLeagueResponse(**response_data)
        
        logger.info(f"Successfully retrieved league: {league_id}")
        metrics.add_metric(name="LeagueRetrieved", unit="Count", value=1)
        
        return success_response(
            data=validated_response.dict(),
            status_code=200
        )
    
    except UnauthorizedError as e:
        logger.warning(f"Unauthorized: {e.message}")
        metrics.add_metric(name="LeagueGetUnauthorized", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except NotFoundError as e:
        logger.warning(f"Not found: {e.message}")
        metrics.add_metric(name="LeagueGetNotFound", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except MultiPlayerException as e:
        logger.warning(f"Application error: {e.message}")
        metrics.add_metric(name="LeagueGetError", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error retrieving league: {str(e)}")
        metrics.add_metric(name="LeagueGetException", unit="Count", value=1)
        return error_response(
            message="Internal server error",
            status_code=500,
            error_code="INTERNAL_ERROR"
        )
