"""Get user profile Lambda function - Pattern #1."""
import json
import os
import uuid
from typing import Optional, Dict, Any

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from pydantic import BaseModel, Field, validator
import boto3

from common.repository.user import UserRepository
from common.utils.responses import success_response, error_response
from common.utils.exceptions import NotFoundError, UnauthorizedError, MultiPlayerException

logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Initialize repository
user_repo = UserRepository()


class GetProfileResponse(BaseModel):
    """Response model for get profile."""
    
    user_id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    account_status: str
    created_at: str
    updated_at: str


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Get current user's profile.
    
    Access Pattern #1: Get user profile
    
    This handler retrieves the authenticated user's profile information from DynamoDB.
    The user ID is extracted from Cognito claims in the authorization context.
    
    Args:
        event: API Gateway Lambda proxy integration event
        context: Lambda context object
    
    Returns:
        API Gateway response with user profile data or error
        
    Raises:
        UnauthorizedError: If user is not authenticated
        NotFoundError: If user profile not found
        MultiPlayerException: For other application errors
    
    Example:
        GET /users/profile
        
        Response (200):
        {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "name": "John Doe",
            "avatar_url": "https://example.com/avatar.jpg",
            "bio": "Fantasy football enthusiast",
            "country": "US",
            "timezone": "America/New_York",
            "account_status": "ACTIVE",
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-20T14:45:00"
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
        
        logger.info(f"Retrieving profile for user: {user_id}")
        metrics.add_metric(name="ProfileRequest", unit="Count", value=1)
        
        # Get user profile from repository
        profile = user_repo.get_profile(user_id)
        
        if not profile:
            logger.warning(f"Profile not found for user: {user_id}")
            raise NotFoundError(f"User profile not found for user {user_id}")
        
        # Build response
        response_data = {
            'user_id': profile.get('user_id'),
            'email': profile.get('email'),
            'name': profile.get('name'),
            'avatar_url': profile.get('avatar_url'),
            'bio': profile.get('bio'),
            'country': profile.get('country'),
            'timezone': profile.get('timezone'),
            'account_status': profile.get('account_status', 'ACTIVE'),
            'created_at': profile.get('created_at'),
            'updated_at': profile.get('updated_at')
        }
        
        # Validate response
        validated_response = GetProfileResponse(**response_data)
        
        logger.info(f"Successfully retrieved profile for user: {user_id}")
        metrics.add_metric(name="ProfileRetrieved", unit="Count", value=1)
        
        return success_response(
            data=validated_response.dict(),
            status_code=200
        )
    
    except UnauthorizedError as e:
        logger.warning(f"Unauthorized: {e.message}")
        metrics.add_metric(name="ProfileUnauthorized", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except NotFoundError as e:
        logger.warning(f"Not found: {e.message}")
        metrics.add_metric(name="ProfileNotFound", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except MultiPlayerException as e:
        logger.warning(f"Application error: {e.message}")
        metrics.add_metric(name="ProfileError", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error retrieving profile: {str(e)}")
        metrics.add_metric(name="ProfileException", unit="Count", value=1)
        return error_response(
            message="Internal server error",
            status_code=500,
            error_code="INTERNAL_ERROR"
        )
