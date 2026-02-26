"""Sign up Lambda function."""
import json
import os
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
import boto3

logger = Logger()
tracer = Tracer()
metrics = Metrics()

cognito_client = boto3.client('cognito-idp')


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Handle user sign up.
    
    Expected body:
    {
        "email": "user@example.com",
        "password": "SecurePassword123",
        "name": "John Doe"
    }
    """
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        password = body.get('password')
        name = body.get('name')
        
        if not all([email, password, name]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields: email, password, name'})
            }
        
        user_pool_id = os.environ.get('USER_POOL_ID')
        
        # Create user in Cognito
        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            TemporaryPassword=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'name', 'Value': name},
                {'Name': 'email_verified', 'Value': 'true'}
            ],
            MessageAction='SUPPRESS'
        )
        
        # Set permanent password
        cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=password,
            Permanent=True
        )
        
        logger.info(f"User created: {email}")
        metrics.add_metric(name="UserSignUp", unit="Count", value=1)
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'User created successfully',
                'userId': response['User']['Username']
            })
        }
    
    except cognito_client.exceptions.UsernameExistsException:
        logger.warning(f"User already exists: {body.get('email')}")
        return {
            'statusCode': 409,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'User already exists'})
        }
    
    except Exception as e:
        logger.exception(f"Error creating user: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }
