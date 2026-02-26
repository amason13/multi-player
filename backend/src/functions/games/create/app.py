"""Create game Lambda function - Pattern #8."""
import json
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

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


class GameType(str, Enum):
    """Game type enumeration."""
    POINTS_BASED = "POINTS_BASED"
    LAST_MAN_STANDING = "LAST_MAN_STANDING"


class CreateGameRequest(BaseModel):
    """Request model for creating a game."""
    
    league_id: str = Field(..., description="League ID (UUID)")
    name: str = Field(..., min_length=1, max_length=200, description="Game name")
    description: Optional[str] = Field(None, max_length=1000, description="Game description")
    game_type: GameType = Field(..., description="Game type (POINTS_BASED or LAST_MAN_STANDING)")
    sport: str = Field(default="football", max_length=50, description="Sport type")
    max_rounds: Optional[int] = Field(None, ge=1, description="Maximum rounds in game")
    rules: Optional[Dict[str, Any]] = Field(None, description="Game-specific rules")
    
    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate game name."""
        if not v or not v.strip():
            raise ValueError("Game name cannot be empty")
        return v.strip()
    
    @validator('game_type', pre=True)
    def validate_game_type(cls, v: str) -> str:
        """Validate game type."""
        if v not in [gt.value for gt in GameType]:
            raise ValueError(f"Invalid game type: {v}")
        return v


class CreateGameResponse(BaseModel):
    """Response model for game creation."""
    
    message: str
    game: Dict[str, Any]


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Create a new game within a league.
    
    Pattern #8: Create game
    
    Expected body:
    {
        "league_id": "league-uuid",
        "name": "Premier League 2024-25",
        "description": "Main points-based competition",
        "game_type": "POINTS_BASED",
        "sport": "football",
        "max_rounds": 38,
        "rules": {
            "points_for_correct_result": 5,
            "points_for_exact_score": 10
        }
    }
    
    Returns:
        API Gateway response with created game details
    """
    try:
        # Extract user ID from Cognito claims
        user_id = event['requestContext']['authorizer']['claims']['sub']
        logger.info(f"Creating game for user: {user_id}")
        
        # Parse and validate request body
        body = json.loads(event.get('body', '{}'))
        request = CreateGameRequest(**body)
        
        # Verify user is league owner/admin
        league = table.get_item(
            Key={
                'PK': f'LEAGUE#{request.league_id}',
                'SK': 'METADATA'
            }
        )
        
        if not league.get('Item'):
            logger.warning(f"League not found: {request.league_id}")
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'League not found',
                    'errorCode': 'LEAGUE_NOT_FOUND'
                })
            }
        
        league_item = league['Item']
        if league_item.get('owner_id') != user_id:
            logger.warning(f"User {user_id} not authorized to create game in league {request.league_id}")
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Only league owner can create games',
                    'errorCode': 'UNAUTHORIZED'
                })
            }
        
        # Generate IDs and timestamps
        game_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Create game metadata item
        game_item = {
            'PK': f'GAME#{game_id}',
            'SK': 'METADATA',
            'GSI1PK': f'LEAGUE#{request.league_id}',
            'GSI1SK': f'GAME#{game_id}',
            'entity_type': 'GAME',
            'game_id': game_id,
            'league_id': request.league_id,
            'name': request.name,
            'description': request.description or '',
            'game_type': request.game_type.value,
            'sport': request.sport,
            'owner_id': user_id,
            'status': 'ACTIVE',
            'current_round': 0,
            'max_rounds': request.max_rounds,
            'member_count': 0,
            'round_count': 0,
            'rules': request.rules or {},
            'created_at': now,
            'updated_at': now
        }
        
        # Create league-game relationship item
        league_game_item = {
            'PK': f'LEAGUE#{request.league_id}',
            'SK': f'GAME#{game_id}',
            'entity_type': 'LEAGUE_GAME',
            'game_id': game_id,
            'league_id': request.league_id,
            'game_type': request.game_type.value,
            'created_at': now,
            'updated_at': now
        }
        
        # Write items to DynamoDB
        with table.batch_writer() as batch:
            batch.put_item(Item=game_item)
            batch.put_item(Item=league_game_item)
        
        logger.info(f"Game created: {game_id} in league {request.league_id}")
        metrics.add_metric(name="GameCreated", unit="Count", value=1)
        metrics.add_metric(name=f"GameType_{request.game_type.value}", unit="Count", value=1)
        
        # Build response
        response_data = {
            'message': 'Game created successfully',
            'game': {
                'id': game_id,
                'league_id': request.league_id,
                'name': request.name,
                'description': request.description,
                'game_type': request.game_type.value,
                'sport': request.sport,
                'owner_id': user_id,
                'status': 'ACTIVE',
                'current_round': 0,
                'max_rounds': request.max_rounds,
                'member_count': 0,
                'round_count': 0,
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
        logger.exception(f"Error creating game: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'errorCode': 'INTERNAL_ERROR'
            })
        }
