"""Unit tests for custom exceptions and response helpers."""
import pytest
import json
from utils.exceptions import (
    MultiPlayerException, ValidationError, NotFoundError,
    UnauthorizedError, ConflictError
)
from utils.responses import success_response, error_response


class TestMultiPlayerException:
    """Test cases for MultiPlayerException base class."""
    
    def test_exception_creation(self):
        """Test creating a MultiPlayerException."""
        exc = MultiPlayerException(
            message='Test error',
            status_code=400,
            error_code='TEST_ERROR'
        )
        assert exc.message == 'Test error'
        assert exc.status_code == 400
        assert exc.error_code == 'TEST_ERROR'
    
    def test_exception_default_values(self):
        """Test MultiPlayerException with default values."""
        exc = MultiPlayerException('Test error')
        assert exc.message == 'Test error'
        assert exc.status_code == 400
        assert exc.error_code == 'INTERNAL_ERROR'
    
    def test_exception_string_representation(self):
        """Test string representation of exception."""
        exc = MultiPlayerException('Test error')
        assert str(exc) == 'Test error'
    
    def test_exception_inheritance(self):
        """Test that MultiPlayerException inherits from Exception."""
        exc = MultiPlayerException('Test error')
        assert isinstance(exc, Exception)


class TestValidationError:
    """Test cases for ValidationError."""
    
    def test_validation_error_creation(self):
        """Test creating a ValidationError."""
        exc = ValidationError('Invalid input')
        assert exc.message == 'Invalid input'
        assert exc.status_code == 400
        assert exc.error_code == 'VALIDATION_ERROR'
    
    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from MultiPlayerException."""
        exc = ValidationError('Invalid input')
        assert isinstance(exc, MultiPlayerException)
    
    def test_validation_error_in_try_except(self):
        """Test catching ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError('Invalid email format')
        
        assert exc_info.value.message == 'Invalid email format'
        assert exc_info.value.status_code == 400


class TestNotFoundError:
    """Test cases for NotFoundError."""
    
    def test_not_found_error_creation(self):
        """Test creating a NotFoundError."""
        exc = NotFoundError('User not found')
        assert exc.message == 'User not found'
        assert exc.status_code == 404
        assert exc.error_code == 'NOT_FOUND'
    
    def test_not_found_error_inheritance(self):
        """Test that NotFoundError inherits from MultiPlayerException."""
        exc = NotFoundError('User not found')
        assert isinstance(exc, MultiPlayerException)
    
    def test_not_found_error_in_try_except(self):
        """Test catching NotFoundError."""
        with pytest.raises(NotFoundError) as exc_info:
            raise NotFoundError('League not found')
        
        assert exc_info.value.message == 'League not found'
        assert exc_info.value.status_code == 404


class TestUnauthorizedError:
    """Test cases for UnauthorizedError."""
    
    def test_unauthorized_error_creation(self):
        """Test creating an UnauthorizedError."""
        exc = UnauthorizedError('Invalid credentials')
        assert exc.message == 'Invalid credentials'
        assert exc.status_code == 401
        assert exc.error_code == 'UNAUTHORIZED'
    
    def test_unauthorized_error_default_message(self):
        """Test UnauthorizedError with default message."""
        exc = UnauthorizedError()
        assert exc.message == 'Unauthorized'
        assert exc.status_code == 401
    
    def test_unauthorized_error_inheritance(self):
        """Test that UnauthorizedError inherits from MultiPlayerException."""
        exc = UnauthorizedError()
        assert isinstance(exc, MultiPlayerException)
    
    def test_unauthorized_error_in_try_except(self):
        """Test catching UnauthorizedError."""
        with pytest.raises(UnauthorizedError) as exc_info:
            raise UnauthorizedError('Token expired')
        
        assert exc_info.value.message == 'Token expired'
        assert exc_info.value.status_code == 401


class TestConflictError:
    """Test cases for ConflictError."""
    
    def test_conflict_error_creation(self):
        """Test creating a ConflictError."""
        exc = ConflictError('User already exists')
        assert exc.message == 'User already exists'
        assert exc.status_code == 409
        assert exc.error_code == 'CONFLICT'
    
    def test_conflict_error_inheritance(self):
        """Test that ConflictError inherits from MultiPlayerException."""
        exc = ConflictError('User already exists')
        assert isinstance(exc, MultiPlayerException)
    
    def test_conflict_error_in_try_except(self):
        """Test catching ConflictError."""
        with pytest.raises(ConflictError) as exc_info:
            raise ConflictError('Email already registered')
        
        assert exc_info.value.message == 'Email already registered'
        assert exc_info.value.status_code == 409


class TestSuccessResponse:
    """Test cases for success_response helper."""
    
    def test_success_response_default(self):
        """Test creating a default success response."""
        response = success_response({'message': 'Success'})
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        body = json.loads(response['body'])
        assert body['message'] == 'Success'
    
    def test_success_response_201(self):
        """Test creating a 201 success response."""
        response = success_response({'id': '123'}, status_code=201)
        
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['id'] == '123'
    
    def test_success_response_with_custom_headers(self):
        """Test success response with custom headers."""
        custom_headers = {'X-Custom-Header': 'custom-value'}
        response = success_response(
            {'message': 'Success'},
            headers=custom_headers
        )
        
        assert response['headers']['X-Custom-Header'] == 'custom-value'
        assert response['headers']['Content-Type'] == 'application/json'
    
    def test_success_response_with_dict_body(self):
        """Test success response with dictionary body."""
        data = {
            'user': {
                'id': '123',
                'name': 'Test User',
                'email': 'test@example.com'
            }
        }
        response = success_response(data)
        
        body = json.loads(response['body'])
        assert body['user']['id'] == '123'
        assert body['user']['name'] == 'Test User'
    
    def test_success_response_with_list_body(self):
        """Test success response with list body."""
        data = [
            {'id': '1', 'name': 'Item 1'},
            {'id': '2', 'name': 'Item 2'}
        ]
        response = success_response(data)
        
        body = json.loads(response['body'])
        assert len(body) == 2
        assert body[0]['id'] == '1'
    
    def test_success_response_with_string_body(self):
        """Test success response with string body."""
        response = success_response('{"message": "Success"}')
        
        assert response['body'] == '{"message": "Success"}'
    
    def test_success_response_cors_headers(self):
        """Test that success response includes CORS headers."""
        response = success_response({'message': 'Success'})
        
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'


class TestErrorResponse:
    """Test cases for error_response helper."""
    
    def test_error_response_default(self):
        """Test creating a default error response."""
        response = error_response('Bad Request')
        
        assert response['statusCode'] == 400
        assert response['headers']['Content-Type'] == 'application/json'
        
        body = json.loads(response['body'])
        assert body['error'] == 'Bad Request'
        assert body['statusCode'] == 400
    
    def test_error_response_with_error_code(self):
        """Test error response with error code."""
        response = error_response(
            'Invalid input',
            status_code=400,
            error_code='VALIDATION_ERROR'
        )
        
        body = json.loads(response['body'])
        assert body['error'] == 'Invalid input'
        assert body['errorCode'] == 'VALIDATION_ERROR'
    
    def test_error_response_401(self):
        """Test creating a 401 error response."""
        response = error_response(
            'Unauthorized',
            status_code=401,
            error_code='UNAUTHORIZED'
        )
        
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert body['error'] == 'Unauthorized'
    
    def test_error_response_404(self):
        """Test creating a 404 error response."""
        response = error_response(
            'Not Found',
            status_code=404,
            error_code='NOT_FOUND'
        )
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error'] == 'Not Found'
    
    def test_error_response_500(self):
        """Test creating a 500 error response."""
        response = error_response(
            'Internal Server Error',
            status_code=500,
            error_code='INTERNAL_ERROR'
        )
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['error'] == 'Internal Server Error'
    
    def test_error_response_with_custom_headers(self):
        """Test error response with custom headers."""
        custom_headers = {'X-Error-ID': 'error-123'}
        response = error_response(
            'Bad Request',
            headers=custom_headers
        )
        
        assert response['headers']['X-Error-ID'] == 'error-123'
        assert response['headers']['Content-Type'] == 'application/json'
    
    def test_error_response_without_error_code(self):
        """Test error response without error code."""
        response = error_response('Bad Request', status_code=400)
        
        body = json.loads(response['body'])
        assert 'errorCode' not in body
        assert body['error'] == 'Bad Request'
    
    def test_error_response_cors_headers(self):
        """Test that error response includes CORS headers."""
        response = error_response('Bad Request')
        
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'


class TestExceptionToResponseMapping:
    """Test cases for mapping exceptions to responses."""
    
    def test_validation_error_to_response(self):
        """Test converting ValidationError to response."""
        exc = ValidationError('Invalid email')
        response = error_response(
            exc.message,
            status_code=exc.status_code,
            error_code=exc.error_code
        )
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['errorCode'] == 'VALIDATION_ERROR'
    
    def test_not_found_error_to_response(self):
        """Test converting NotFoundError to response."""
        exc = NotFoundError('User not found')
        response = error_response(
            exc.message,
            status_code=exc.status_code,
            error_code=exc.error_code
        )
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['errorCode'] == 'NOT_FOUND'
    
    def test_unauthorized_error_to_response(self):
        """Test converting UnauthorizedError to response."""
        exc = UnauthorizedError('Invalid token')
        response = error_response(
            exc.message,
            status_code=exc.status_code,
            error_code=exc.error_code
        )
        
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert body['errorCode'] == 'UNAUTHORIZED'
    
    def test_conflict_error_to_response(self):
        """Test converting ConflictError to response."""
        exc = ConflictError('Email already exists')
        response = error_response(
            exc.message,
            status_code=exc.status_code,
            error_code=exc.error_code
        )
        
        assert response['statusCode'] == 409
        body = json.loads(response['body'])
        assert body['errorCode'] == 'CONFLICT'


class TestResponseFormatting:
    """Test cases for response formatting."""
    
    def test_response_body_is_json_string(self):
        """Test that response body is a JSON string."""
        response = success_response({'message': 'Success'})
        
        assert isinstance(response['body'], str)
        # Should be valid JSON
        json.loads(response['body'])
    
    def test_response_headers_are_dict(self):
        """Test that response headers are a dictionary."""
        response = success_response({'message': 'Success'})
        
        assert isinstance(response['headers'], dict)
        assert 'Content-Type' in response['headers']
    
    def test_response_status_code_is_int(self):
        """Test that response status code is an integer."""
        response = success_response({'message': 'Success'})
        
        assert isinstance(response['statusCode'], int)
        assert response['statusCode'] == 200
    
    def test_response_structure(self):
        """Test that response has correct structure."""
        response = success_response({'message': 'Success'})
        
        assert 'statusCode' in response
        assert 'headers' in response
        assert 'body' in response
        assert len(response) == 3


class TestErrorHandlingScenarios:
    """Test cases for error handling scenarios."""
    
    def test_handle_validation_error(self):
        """Test handling validation error in try-except."""
        try:
            raise ValidationError('Email is required')
        except ValidationError as e:
            response = error_response(
                e.message,
                status_code=e.status_code,
                error_code=e.error_code
            )
            assert response['statusCode'] == 400
    
    def test_handle_not_found_error(self):
        """Test handling not found error in try-except."""
        try:
            raise NotFoundError('User not found')
        except NotFoundError as e:
            response = error_response(
                e.message,
                status_code=e.status_code,
                error_code=e.error_code
            )
            assert response['statusCode'] == 404
    
    def test_handle_unauthorized_error(self):
        """Test handling unauthorized error in try-except."""
        try:
            raise UnauthorizedError('Token expired')
        except UnauthorizedError as e:
            response = error_response(
                e.message,
                status_code=e.status_code,
                error_code=e.error_code
            )
            assert response['statusCode'] == 401
    
    def test_handle_conflict_error(self):
        """Test handling conflict error in try-except."""
        try:
            raise ConflictError('Email already registered')
        except ConflictError as e:
            response = error_response(
                e.message,
                status_code=e.status_code,
                error_code=e.error_code
            )
            assert response['statusCode'] == 409
    
    def test_handle_generic_exception(self):
        """Test handling generic exception."""
        try:
            raise Exception('Unexpected error')
        except Exception as e:
            response = error_response(
                'Internal Server Error',
                status_code=500,
                error_code='INTERNAL_ERROR'
            )
            assert response['statusCode'] == 500
