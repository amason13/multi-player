"""List league members Lambda function - Pattern #5."""
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


class LeagueMember(BaseModel):
    """League member item."""
    
    user_id: str
    role: str
    joined_at: str


class ListMembersResponse(BaseModel):
    """Response model for list members."""
    
    members: List[LeagueMember]
    count: int


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """List all members of a league.
    
    Access Pattern #5: Get league members
    
    This handler retrieves all members of a specific league.
    The user must be authenticated and a member of the league to access it.
    
    Path Parameters:
        leagueId: The ID of the league
    
    Query Parameters:
        limit (optional): Maximum number of members to return (default: 20, max: 100)
        offset (optional): Number of members to skip for pagination (default: 0)
    
    Args:
        event: API Gateway Lambda proxy integration event
        context: Lambda context object
    
    Returns:
        API Gateway response with list of league members or error
        
    Raises:
        UnauthorizedError: If user is not authenticated
        NotFoundError: If league not found
        MultiPlayerException: For other application errors
    
    Example:
        GET /leagues/{leagueId}/members?limit=20&offset=0
        
        Response (200):
        {
            "members": [
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440001",
                    "role": "owner",
                    "joined_at": "2024-01-01T00:00:00"
                },
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440002",
                    "role": "member",
                    "joined_at": "2024-01-05T10:30:00"
                }
            ],
            "count": 2
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
        limit = int(query_params.get('limit', 20))
        offset = int(query_params.get('offset', 0))
        
        # Validate pagination parameters
        limit = min(max(limit, 1), 100)  # Clamp between 1 and 100
        offset = max(offset, 0)
        
        logger.info(f"Listing members for league: {league_id} (limit={limit}, offset={offset})")
        metrics.add_metric(name="MembersListRequest", unit="Count", value=1)
        
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
        
        # Get league members from repository
        all_members = league_repo.get_members(league_id, limit=limit + offset)
        
        # Apply offset
        paginated_members = all_members[offset:offset + limit]
        
        # Build response
        members_data = []
        for member in paginated_members:
            members_data.append({
                'user_id': member.get('user_id'),
                'role': member.get('role'),
                'joined_at': member.get('joined_at')
            })
        
        # Validate response
        validated_members = [LeagueMember(**member) for member in members_data]
        response_data = ListMembersResponse(
            members=validated_members,
            count=len(validated_members)
        )
        
        logger.info(f"Retrieved {len(validated_members)} members for league: {league_id}")
        metrics.add_metric(name="MembersListed", unit="Count", value=len(validated_members))
        
        return success_response(
            data=response_data.dict(),
            status_code=200
        )
    
    except UnauthorizedError as e:
        logger.warning(f"Unauthorized: {e.message}")
        metrics.add_metric(name="MembersListUnauthorized", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except NotFoundError as e:
        logger.warning(f"Not found: {e.message}")
        metrics.add_metric(name="MembersListNotFound", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except MultiPlayerException as e:
        logger.warning(f"Application error: {e.message}")
        metrics.add_metric(name="MembersListError", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error listing members: {str(e)}")
        metrics.add_metric(name="MembersListException", unit="Count", value=1)
        return error_response(
            message="Internal server error",
            status_code=500,
            error_code="INTERNAL_ERROR"
        )
