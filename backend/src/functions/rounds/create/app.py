"""Create round Lambda function - Pattern #11."""
import json
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
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


class RoundStatus(str, Enum):
    """Round status enumeration."""
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Match(BaseModel):
    """Match model for round."""
    
    match_id: str = Field(..., description="Match ID")
    home_team: str = Field(..., min_length=1, max_length=100, description="Home team name")
    away_team: str = Field(..., min_length=1, max_length=100, description="Away team name")
    home_team_id: Optional[str] = Field(None, description="Home team external ID")
    away_team_id: Optional[str] = Field(None, description="Away team external ID")
    match_date: str = Field(..., description="Match date/time (ISO 8601)")
    venue: Optional[str] = Field(None, max_length=200, description="Match venue")
    is_featured: bool = Field(default=False, description="Is featured match")
    is_bonus_match: bool = Field(default=False, description="Is bonus points match")
    bonus_multiplier: float = Field(default=1.0, ge=1.0, le=5.0, description="Bonus points multiplier")


class CreateRoundRequest(BaseModel):
    """Request model for creating a round."""
    
    game_id: str = Field(..., description="Game ID (UUID)")
    league_id: str = Field(..., description="League ID (UUID)")
    round_number: int = Field(..., ge=1, description="Round number (sequential)")
    title: Optional[str] = Field(None, max_length=200, description="Round title")
    description: Optional[str] = Field(None, max_length=1000, description="Round description")
    start_date: str = Field(..., description="Round start date (ISO 8601)")
    end_date: str = Field(..., description="Round end date (ISO 8601)")
    prediction_deadline: str = Field(..., description="Prediction deadline (ISO 8601)")
    scoring_start_date: str = Field(..., description="Scoring start date (ISO 8601)")
    scoring_end_date: str = Field(..., description="Scoring end date (ISO 8601)")
    matches: List[Match] = Field(..., min_items=1, description="List of matches in round")
    is_playoff_round: bool = Field(default=False, description="Is playoff round")
    is_final_round: bool = Field(default=False, description="Is final round")
    
    @validator('title')
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title."""
        if v and not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip() if v else None
    
    @validator('start_date', 'end_date', 'prediction_deadline', 'scoring_start_date', 'scoring_end_date')
    def validate_dates(cls, v: str) -> str:
        """Validate ISO 8601 date format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Invalid ISO 8601 date format: {v}")
        return v


class CreateRoundResponse(BaseModel):
    """Response model for round creation."""
    
    message: str
    round: Dict[str, Any]


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Create a new round within a game.
    
    Pattern #11: Create round
    
    Expected body:
    {
        "game_id": "game-uuid",
        "league_id": "league-uuid",
        "round_number": 1,
        "title": "Week 1: Premier League Matchday 1",
        "description": "First week of the season",
        "start_date": "2024-02-10T00:00:00Z",
        "end_date": "2024-02-17T23:59:59Z",
        "prediction_deadline": "2024-02-10T12:00:00Z",
        "scoring_start_date": "2024-02-10T15:00:00Z",
        "scoring_end_date": "2024-02-17T23:59:59Z",
        "matches": [
            {
                "match_id": "match-001",
                "home_team": "Manchester United",
                "away_team": "Liverpool",
                "match_date": "2024-02-10T15:00:00Z",
                "is_featured": true
            }
        ]
    }
    
    Returns:
        API Gateway response with created round details
    """
    try:
        # Extract user ID from Cognito claims
        user_id = event['requestContext']['authorizer']['claims']['sub']
        logger.info(f"Creating round for user: {user_id}")
        
        # Parse and validate request body
        body = json.loads(event.get('body', '{}'))
        request = CreateRoundRequest(**body)
        
        # Verify user is game owner/admin
        game = table.get_item(
            Key={
                'PK': f'GAME#{request.game_id}',
                'SK': 'METADATA'
            }
        )
        
        if not game.get('Item'):
            logger.warning(f"Game not found: {request.game_id}")
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Game not found',
                    'errorCode': 'GAME_NOT_FOUND'
                })
            }
        
        game_item = game['Item']
        if game_item.get('owner_id') != user_id:
            logger.warning(f"User {user_id} not authorized to create round in game {request.game_id}")
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Only game owner can create rounds',
                    'errorCode': 'UNAUTHORIZED'
                })
            }
        
        # Generate IDs and timestamps
        round_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Create round metadata item
        round_item = {
            'PK': f'GAME#{request.game_id}',
            'SK': f'ROUND#{request.round_number}',
            'GSI1PK': f'LEAGUE#{request.league_id}',
            'GSI1SK': f'ROUND#{request.round_number}',
            'entity_type': 'ROUND',
            'round_id': round_id,
            'game_id': request.game_id,
            'league_id': request.league_id,
            'round_number': request.round_number,
            'title': request.title or f'Round {request.round_number}',
            'description': request.description or '',
            'status': RoundStatus.SCHEDULED.value,
            'start_date': request.start_date,
            'end_date': request.end_date,
            'prediction_deadline': request.prediction_deadline,
            'scoring_start_date': request.scoring_start_date,
            'scoring_end_date': request.scoring_end_date,
            'match_count': len(request.matches),
            'total_predictions': 0,
            'completed_predictions': 0,
            'prediction_completion_rate': 0.0,
            'is_playoff_round': request.is_playoff_round,
            'is_final_round': request.is_final_round,
            'created_at': now,
            'updated_at': now
        }
        
        # Create match items
        match_items = []
        for match in request.matches:
            match_item = {
                'PK': f'GAME#{request.game_id}',
                'SK': f'ROUND#{request.round_number}#MATCH#{match.match_id}',
                'entity_type': 'ROUND_MATCH',
                'match_id': match.match_id,
                'round_id': round_id,
                'game_id': request.game_id,
                'league_id': request.league_id,
                'round_number': request.round_number,
                'home_team': match.home_team,
                'away_team': match.away_team,
                'home_team_id': match.home_team_id,
                'away_team_id': match.away_team_id,
                'match_date': match.match_date,
                'match_status': 'SCHEDULED',
                'prediction_count': 0,
                'prediction_deadline': request.prediction_deadline,
                'is_featured': match.is_featured,
                'is_bonus_match': match.is_bonus_match,
                'bonus_multiplier': match.bonus_multiplier,
                'venue': match.venue,
                'created_at': now,
                'updated_at': now
            }
            match_items.append(match_item)
        
        # Write items to DynamoDB
        with table.batch_writer() as batch:
            batch.put_item(Item=round_item)
            for match_item in match_items:
                batch.put_item(Item=match_item)
        
        logger.info(f"Round created: {round_id} (round #{request.round_number}) in game {request.game_id}")
        metrics.add_metric(name="RoundCreated", unit="Count", value=1)
        metrics.add_metric(name="MatchesCreated", unit="Count", value=len(request.matches))
        
        # Build response
        response_data = {
            'message': 'Round created successfully',
            'round': {
                'id': round_id,
                'game_id': request.game_id,
                'league_id': request.league_id,
                'round_number': request.round_number,
                'title': round_item['title'],
                'description': request.description,
                'status': RoundStatus.SCHEDULED.value,
                'start_date': request.start_date,
                'end_date': request.end_date,
                'prediction_deadline': request.prediction_deadline,
                'match_count': len(request.matches),
                'is_playoff_round': request.is_playoff_round,
                'is_final_round': request.is_final_round,
                'created_at': now,
                'updated_at': now,
                'matches': [
                    {
                        'id': m.match_id,
                        'home_team': m.home_team,
                        'away_team': m.away_team,
                        'match_date': m.match_date,
                        'is_featured': m.is_featured,
                        'is_bonus_match': m.is_bonus_match,
                        'bonus_multiplier': m.bonus_multiplier
                    }
                    for m in request.matches
                ]
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
        logger.exception(f"Error creating round: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'errorCode': 'INTERNAL_ERROR'
            })
        }
