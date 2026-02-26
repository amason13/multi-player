"""Create league Lambda function - Pattern #3."""
import json
import os
import uuid
from datetime import datetime
from typing import Optional

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from pydantic import BaseModel, Field, validator
import boto3

logger = Logger()
tracer = Tracer()
metrics = Metrics()

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TABLE_NAME'))


class CreateLeagueRequest(BaseModel):
    """Request model for creating a league."""
    
    name: str = Field(..., min_length=1, max_length=200, description="League name")
    description: Optional[str] = Field(None, max_length=1000, description="League description")
    sport: str = Field(default="football", max_length=50, description="Sport type")
    
    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate league name."""
        if not v or not v.strip():
            raise ValueError("League name cannot be empty")
        return v.strip()


class CreateLeagueResponse(BaseModel):
    """Response model for league creation."""
    
    message: str
    league: dict


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Create a new league.
    
    Pattern #3: Create league
    
    Expected body:
    {
        "name": "Premier League 2024",
        "description": "Fantasy football league",
        "sport": "football"
    }
    
    Returns:
        API Gateway response with created league details
    """
    try:
        # Extract user ID from Cognito claims
        user_id = event['requestContext']['authorizer']['claims']['sub']
        logger.info(f"Creating league for user: {user_id}")
        
        # Parse and validate request body
        body = json.loads(event.get('body', '{}'))
        request = CreateLeagueRequest(**body)
        
        # Generate IDs and timestamps
        league_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Create league metadata item
        league_item = {
            'PK': f'LEAGUE#{league_id}',
            'SK': 'METADATA',
            'GSI1PK': f'USER#{user_id}',
            'GSI1SK': f'LEAGUE#{league_id}',
            'entity_type': 'LEAGUE',
            'league_id': league_id,
            'name': request.name,
            'description': request.description or '',
            'sport': request.sport,
            'owner_id': user_id,
            'status': 'ACTIVE',
            'member_count': 1,
            'game_count': 0,
            'created_at': now,
            'updated_at': now
        }
        
        # Add owner as first member
        member_item = {
            'PK': f'LEAGUE#{league_id}',
            'SK': f'MEMBER#{user_id}',
            'entity_type': 'LEAGUE_MEMBER',
            'user_id': user_id,
            'role': 'owner',
            'joined_at': now,
            'created_at': now,
            'updated_at': now
        }
        
        # Write both items to DynamoDB
        with table.batch_writer() as batch:
            batch.put_item(Item=league_item)
            batch.put_item(Item=member_item)
        
        logger.info(f"League created: {league_id} by user {user_id}")
        metrics.add_metric(name="LeagueCreated", unit="Count", value=1)
        
        # Build response
        response_data = {
            'message': 'League created successfully',
            'league': {
                'id': league_id,
                'name': request.name,
                'description': request.description,
                'sport': request.sport,
                'owner_id': user_id,
                'status': 'ACTIVE',
                'member_count': 1,
                'game_count': 0,
                'created_at': now,
                'updated_at': now
            }
        }
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response_data)
        }
    
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': f'Validation error: {str(e)}',
                'errorCode': 'VALIDATION_ERROR'
            })
        }
    
    except KeyError as e:
        logger.warning(f"Missing required field: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': f'Missing required field: {str(e)}',
                'errorCode': 'MISSING_FIELD'
            })
        }
    
    except Exception as e:
        logger.exception(f"Error creating league: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'errorCode': 'INTERNAL_ERROR'
            })
        }
