"""List user's leagues Lambda function - Pattern #2."""
import json
import os
from typing import Optional, List, Dict, Any

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from pydantic import BaseModel, Field

from common.repository.league import LeagueRepository
from common.utils.responses import success_response, error_response
from common.utils.exceptions import UnauthorizedError, MultiPlayerException

logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Initialize repository
league_repo = LeagueRepository()


class LeagueListItem(BaseModel):
    """League item in list response."""
    
    league_id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    member_count: int
    game_count: int
    status: str
    created_at: str
    updated_at: str


class ListLeaguesResponse(BaseModel):
    """Response model for list leagues."""
    
    leagues: List[LeagueListItem]
    count: int


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """List all leagues for the current user.
    
    Access Pattern #2: Get user's leagues
    
    This handler retrieves all leagues that the authenticated user is a member of.
    The user ID is extracted from Cognito claims in the authorization context.
    
    Query Parameters:
        limit (optional): Maximum number of leagues to return (default: 10, max: 100)
        offset (optional): Number of leagues to skip for pagination (default: 0)
    
    Args:
        event: API Gateway Lambda proxy integration event
        context: Lambda context object
    
    Returns:
        API Gateway response with list of user's leagues or error
        
    Raises:
        UnauthorizedError: If user is not authenticated
        MultiPlayerException: For other application errors
    
    Example:
        GET /users/leagues?limit=20&offset=0
        
        Response (200):
        {
            "leagues": [
                {
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
            ],
            "count": 1
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
        
        # Parse query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        limit = int(query_params.get('limit', 10))
        offset = int(query_params.get('offset', 0))
        
        # Validate pagination parameters
        limit = min(max(limit, 1), 100)  # Clamp between 1 and 100
        offset = max(offset, 0)
        
        logger.info(f"Listing leagues for user: {user_id} (limit={limit}, offset={offset})")
        metrics.add_metric(name="LeaguesListRequest", unit="Count", value=1)
        
        # Get user's leagues from repository
        user_leagues = league_repo.get_user_leagues(user_id, limit=limit + offset)
        
        # Apply offset
        paginated_leagues = user_leagues[offset:offset + limit]
        
        # Build response
        leagues_data = []
        for league_item in paginated_leagues:
            league_id = league_item.get('league_id')
            
            # Get full league details
            league = league_repo.get_league(league_id)
            if league:
                leagues_data.append({
                    'league_id': league.get('league_id'),
                    'name': league.get('name'),
                    'description': league.get('description'),
                    'owner_id': league.get('owner_id'),
                    'member_count': league.get('member_count', 0),
                    'game_count': league.get('game_count', 0),
                    'status': league.get('status', 'ACTIVE'),
                    'created_at': league.get('created_at'),
                    'updated_at': league.get('updated_at')
                })
        
        # Validate response
        validated_leagues = [LeagueListItem(**league) for league in leagues_data]
        response_data = ListLeaguesResponse(
            leagues=validated_leagues,
            count=len(validated_leagues)
        )
        
        logger.info(f"Retrieved {len(validated_leagues)} leagues for user: {user_id}")
        metrics.add_metric(name="LeaguesListed", unit="Count", value=len(validated_leagues))
        
        return success_response(
            data=response_data.dict(),
            status_code=200
        )
    
    except UnauthorizedError as e:
        logger.warning(f"Unauthorized: {e.message}")
        metrics.add_metric(name="LeaguesListUnauthorized", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except MultiPlayerException as e:
        logger.warning(f"Application error: {e.message}")
        metrics.add_metric(name="LeaguesListError", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error listing leagues: {str(e)}")
        metrics.add_metric(name="LeaguesListException", unit="Count", value=1)
        return error_response(
            message="Internal server error",
            status_code=500,
            error_code="INTERNAL_ERROR"
        )
