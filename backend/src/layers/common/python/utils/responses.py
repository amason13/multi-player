"""HTTP response helpers."""
import json
from typing import Any, Dict, Optional


def success_response(
    data: Any,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create successful HTTP response.
    
    Args:
        data: Response body data
        status_code: HTTP status code
        headers: Additional headers
    
    Returns:
        API Gateway response format
    """
    response_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
    }
    if headers:
        response_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': response_headers,
        'body': json.dumps(data) if not isinstance(data, str) else data
    }


def error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create error HTTP response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Application error code
        headers: Additional headers
    
    Returns:
        API Gateway response format
    """
    response_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
    }
    if headers:
        response_headers.update(headers)
    
    body = {
        'error': message,
        'statusCode': status_code
    }
    if error_code:
        body['errorCode'] = error_code
    
    return {
        'statusCode': status_code,
        'headers': response_headers,
        'body': json.dumps(body)
    }
