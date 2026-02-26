"""Submit prediction Lambda function - Pattern #13."""
import json
import os
import uuid
from typing import Optional, Dict, Any

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from pydantic import BaseModel, Field, validator

from common.repository.prediction import PredictionRepository
from common.repository.league import LeagueRepository
from common.utils.responses import success_response, error_response
from common.utils.exceptions import (
    NotFoundError, UnauthorizedError, ValidationError, MultiPlayerException
)

logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Initialize repositories
prediction_repo = PredictionRepository()
league_repo = LeagueRepository()


class SubmitPointsBasedPredictionRequest(BaseModel):
    """Request model for points-based prediction."""
    
    league_id: str = Field(..., description="League ID")
    round_number: int = Field(..., ge=1, description="Round number")
    match_id: str = Field(..., description="Match ID")
    predicted_home_score: int = Field(..., ge=0, description="Predicted home team score")
    predicted_away_score: int = Field(..., ge=0, description="Predicted away team score")
    confidence_level: Optional[int] = Field(None, ge=1, le=10, description="Confidence level 1-10")
    reasoning: Optional[str] = Field(None, max_length=500, description="Prediction reasoning")


class SubmitLMSPredictionRequest(BaseModel):
    """Request model for Last Man Standing prediction."""
    
    league_id: str = Field(..., description="League ID")
    round_number: int = Field(..., ge=1, description="Round number")
    match_id: str = Field(..., description="Match ID")
    predicted_winner: str = Field(..., description="Predicted winner (HOME or AWAY)")
    confidence_level: Optional[int] = Field(None, ge=1, le=10, description="Confidence level 1-10")
    reasoning: Optional[str] = Field(None, max_length=500, description="Prediction reasoning")
    
    @validator('predicted_winner')
    def validate_winner(cls, v: str) -> str:
        """Validate predicted winner."""
        if v not in ['HOME', 'AWAY']:
            raise ValueError("predicted_winner must be HOME or AWAY")
        return v


class PredictionResponse(BaseModel):
    """Response model for prediction submission."""
    
    prediction_id: str
    user_id: str
    league_id: str
    round_number: int
    match_id: str
    game_type: str
    status: str
    created_at: str


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Submit a prediction for a match.
    
    Access Pattern #13: Submit prediction
    
    This handler allows users to submit predictions for matches in a league.
    Supports both points-based and Last Man Standing game types.
    
    The user must be authenticated and a member of the league.
    
    Request Body (Points-Based):
    {
        "league_id": "league-uuid",
        "round_number": 1,
        "match_id": "match-uuid",
        "predicted_home_score": 2,
        "predicted_away_score": 1,
        "confidence_level": 8,
        "reasoning": "Home team is stronger"
    }
    
    Request Body (Last Man Standing):
    {
        "league_id": "league-uuid",
        "round_number": 1,
        "match_id": "match-uuid",
        "predicted_winner": "HOME",
        "confidence_level": 7,
        "reasoning": "Home team has better form"
    }
    
    Args:
        event: API Gateway Lambda proxy integration event
        context: Lambda context object
    
    Returns:
        API Gateway response with prediction details or error
        
    Raises:
        UnauthorizedError: If user is not authenticated
        NotFoundError: If league or match not found
        ValidationError: If input validation fails
        MultiPlayerException: For other application errors
    
    Example:
        POST /predictions/submit
        
        Response (201):
        {
            "prediction_id": "pred-uuid",
            "user_id": "user-uuid",
            "league_id": "league-uuid",
            "round_number": 1,
            "match_id": "match-uuid",
            "game_type": "POINTS_BASED",
            "status": "PENDING",
            "created_at": "2024-01-20T14:45:00"
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
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        league_id = body.get('league_id')
        
        if not league_id:
            raise ValidationError("league_id is required")
        
        logger.info(f"Submitting prediction for user: {user_id}, league: {league_id}")
        metrics.add_metric(name="PredictionSubmitRequest", unit="Count", value=1)
        
        # Verify user is a member of the league
        is_member = league_repo.is_member(league_id, user_id)
        if not is_member:
            logger.warning(f"User {user_id} is not a member of league {league_id}")
            raise NotFoundError(f"League {league_id} not found or access denied")
        
        # Get league to determine game type
        league = league_repo.get_league(league_id)
        if not league:
            logger.warning(f"League not found: {league_id}")
            raise NotFoundError(f"League {league_id} not found")
        
        game_type = body.get('game_type', 'POINTS_BASED')
        prediction_id = str(uuid.uuid4())
        
        # Submit prediction based on game type
        if game_type == 'POINTS_BASED':
            request = SubmitPointsBasedPredictionRequest(**body)
            prediction = prediction_repo.submit_points_based_prediction(
                prediction_id=prediction_id,
                user_id=user_id,
                league_id=request.league_id,
                round_number=request.round_number,
                match_id=request.match_id,
                predicted_home_score=request.predicted_home_score,
                predicted_away_score=request.predicted_away_score,
                confidence_level=request.confidence_level,
                reasoning=request.reasoning
            )
        
        elif game_type == 'LAST_MAN_STANDING':
            request = SubmitLMSPredictionRequest(**body)
            prediction = prediction_repo.submit_lms_prediction(
                prediction_id=prediction_id,
                user_id=user_id,
                league_id=request.league_id,
                round_number=request.round_number,
                match_id=request.match_id,
                predicted_winner=request.predicted_winner,
                confidence_level=request.confidence_level,
                reasoning=request.reasoning
            )
        
        else:
            raise ValidationError(f"Invalid game_type: {game_type}")
        
        # Build response
        response_data = {
            'prediction_id': prediction.get('prediction_id'),
            'user_id': prediction.get('user_id'),
            'league_id': prediction.get('league_id'),
            'round_number': prediction.get('round_number'),
            'match_id': prediction.get('match_id'),
            'game_type': prediction.get('game_type'),
            'status': prediction.get('status'),
            'created_at': prediction.get('created_at')
        }
        
        # Validate response
        validated_response = PredictionResponse(**response_data)
        
        logger.info(f"Prediction submitted: {prediction_id} for user: {user_id}")
        metrics.add_metric(name="PredictionSubmitted", unit="Count", value=1)
        
        return success_response(
            data=validated_response.dict(),
            status_code=201
        )
    
    except UnauthorizedError as e:
        logger.warning(f"Unauthorized: {e.message}")
        metrics.add_metric(name="PredictionSubmitUnauthorized", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except NotFoundError as e:
        logger.warning(f"Not found: {e.message}")
        metrics.add_metric(name="PredictionSubmitNotFound", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        metrics.add_metric(name="PredictionSubmitValidationError", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except MultiPlayerException as e:
        logger.warning(f"Application error: {e.message}")
        metrics.add_metric(name="PredictionSubmitError", unit="Count", value=1)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error submitting prediction: {str(e)}")
        metrics.add_metric(name="PredictionSubmitException", unit="Count", value=1)
        return error_response(
            message="Internal server error",
            status_code=500,
            error_code="INTERNAL_ERROR"
        )
