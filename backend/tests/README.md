# Multi-Player Backend Test Suite

Comprehensive unit tests for the Multi-Player fantasy football platform backend.

## Overview

This test suite provides complete coverage for:
- **Entity Models**: Pydantic validation, serialization, and DynamoDB conversion
- **Repository Classes**: DynamoDB operations with mocked AWS services
- **Lambda Handlers**: Input validation, authorization, and response formatting
- **Error Handling**: Custom exceptions and error response formatting

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures and configuration
├── pytest.ini                           # Pytest configuration
├── requirements.txt                     # Test dependencies
├── unit/
│   ├── test_models.py                  # Entity model tests
│   ├── test_repositories.py            # Repository class tests
│   ├── test_lambda_handlers.py         # Lambda handler tests
│   └── test_exceptions_and_responses.py # Exception and response tests
└── integration/                         # Integration tests (future)
```

## Running Tests

### Install Dependencies

```bash
pip install -r tests/requirements.txt
```

### Run All Tests

```bash
pytest tests/unit -v
```

### Run Specific Test File

```bash
pytest tests/unit/test_models.py -v
```

### Run Specific Test Class

```bash
pytest tests/unit/test_models.py::TestUserProfile -v
```

### Run Specific Test

```bash
pytest tests/unit/test_models.py::TestUserProfile::test_user_profile_creation -v
```

### Run with Coverage

```bash
pytest tests/unit --cov=src/layers/common/python --cov-report=html
```

### Run Tests by Marker

```bash
# Run only model tests
pytest tests/unit -m models -v

# Run only repository tests
pytest tests/unit -m repositories -v

# Run only handler tests
pytest tests/unit -m handlers -v

# Run only exception tests
pytest tests/unit -m exceptions -v
```

## Test Categories

### 1. Entity Models (`test_models.py`)

Tests for Pydantic models and validation:

- **BaseEntity**: Core entity with DynamoDB keys
  - Creation and initialization
  - GSI key handling
  - TTL support
  - DynamoDB serialization
  - DateTime handling

- **UserProfile**: User profile entity
  - Creation with required/optional fields
  - Email validation
  - Name validation and trimming
  - Country code validation (ISO 3166-1)
  - Language code validation (ISO 639-1)
  - Account status enum
  - DynamoDB conversion

- **UserPreferences**: User preferences entity
  - Default values
  - Enum values (visibility, theme, frequency)
  - All customizable fields
  - DynamoDB conversion

- **UserSettings**: User account settings
  - 2FA configuration
  - Session timeout validation
  - IP whitelist support
  - Account deletion tracking
  - DynamoDB conversion

- **UserStatistics**: User statistics per league
  - Points-based statistics
  - Last Man Standing statistics
  - Prediction statistics
  - Automatic calculations (rank change, win %, accuracy)
  - Non-negative value validation
  - DynamoDB conversion

- **Response Models**: API response models
  - UserProfileResponse
  - UserStatisticsResponse

### 2. Repository Classes (`test_repositories.py`)

Tests for DynamoDB operations:

- **DynamoDBTable**: Low-level DynamoDB wrapper
  - Initialization and configuration
  - Get item operations
  - Put item operations
  - Update item operations
  - Delete item operations
  - Query by partition key
  - Query with sort key prefix
  - GSI queries
  - Error handling

- **UserRepository**: User-specific operations
  - Profile CRUD operations
  - Preferences CRUD operations
  - Settings CRUD operations
  - Statistics CRUD operations
  - Batch operations (get_user_data, create_user_complete)
  - User status management (delete, suspend, reactivate)
  - Login tracking
  - Error handling

### 3. Lambda Handlers (`test_lambda_handlers.py`)

Tests for Lambda function handlers:

- **User Profile Handler** (`/api/users/profile`)
  - Get profile success
  - Missing authentication
  - Profile creation from Cognito claims

- **Sign Up Handler** (`/api/auth/signup`)
  - Successful user creation
  - Missing required fields
  - User already exists
  - Invalid email format

- **Sign In Handler** (`/api/auth/signin`)
  - Successful authentication
  - Missing credentials
  - Invalid credentials
  - User not found

- **Create League Handler** (`/api/leagues`)
  - Successful league creation
  - Missing league name
  - Owner assignment
  - Member initialization

- **Get League Handler** (`/api/leagues/{leagueId}`)
  - Get league details
  - Get league members
  - League not found

- **List Leagues Handler** (`/api/leagues`)
  - List user's leagues
  - Empty league list
  - GSI query

### 4. Exceptions and Responses (`test_exceptions_and_responses.py`)

Tests for error handling:

- **Custom Exceptions**
  - MultiPlayerException (base)
  - ValidationError (400)
  - NotFoundError (404)
  - UnauthorizedError (401)
  - ConflictError (409)
  - Exception inheritance
  - Exception attributes

- **Response Helpers**
  - success_response (200, 201, custom status)
  - error_response (400, 401, 404, 409, 500)
  - Custom headers
  - CORS headers
  - Response formatting
  - JSON serialization

- **Exception to Response Mapping**
  - Converting exceptions to HTTP responses
  - Error code mapping
  - Status code mapping

## Fixtures

### Environment Fixtures

- `setup_test_env`: Sets up test environment variables

### DynamoDB Fixtures

- `dynamodb_table`: Creates a mock DynamoDB table
- `dynamodb_table_wrapper`: Creates a DynamoDBTable wrapper instance

### User Model Fixtures

- `user_id`: Generates a test user ID (UUID)
- `league_id`: Generates a test league ID (UUID)
- `valid_user_profile`: Creates a valid UserProfile instance
- `valid_user_preferences`: Creates a valid UserPreferences instance
- `valid_user_settings`: Creates a valid UserSettings instance
- `valid_user_statistics`: Creates a valid UserStatistics instance

### Cognito Fixtures

- `cognito_claims`: Creates mock Cognito claims
- `lambda_event_with_auth`: Creates a Lambda event with Cognito authorization
- `lambda_context`: Creates a mock Lambda context

### Response Fixtures

- `success_response_200`: Creates a 200 success response
- `success_response_201`: Creates a 201 success response
- `error_response_400`: Creates a 400 error response
- `error_response_401`: Creates a 401 error response
- `error_response_404`: Creates a 404 error response
- `error_response_500`: Creates a 500 error response

### Mock Fixtures

- `mock_dynamodb_client`: Creates a mock DynamoDB client
- `mock_cognito_client`: Creates a mock Cognito client
- `mock_logger`: Creates a mock logger

### Sample Data Fixtures

- `sample_dynamodb_item`: Creates a sample DynamoDB user item
- `sample_league_item`: Creates a sample league item
- `sample_league_member_item`: Creates a sample league member item

## Mocking Strategy

### DynamoDB Mocking

Uses `moto` library to mock AWS DynamoDB:

```python
@mock_dynamodb
def test_example():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    # Create and test with mock DynamoDB
```

### Cognito Mocking

Uses `unittest.mock` to mock Cognito operations:

```python
with patch('boto3.client') as mock_client:
    mock_cognito = MagicMock()
    mock_client.return_value = mock_cognito
    # Mock Cognito responses
```

### Lambda Context Mocking

Creates a mock Lambda context with required attributes:

```python
context = Mock()
context.function_name = 'test-function'
context.aws_request_id = 'test-request-id'
# ... other attributes
```

## Test Coverage

Current test coverage includes:

- **Models**: 100+ test cases covering all entity models
- **Repositories**: 50+ test cases covering all CRUD operations
- **Handlers**: 30+ test cases covering all Lambda functions
- **Exceptions**: 40+ test cases covering error handling
- **Responses**: 30+ test cases covering response formatting

**Total**: 250+ test cases

## Best Practices

### 1. Test Organization

- Tests are organized by component (models, repositories, handlers, exceptions)
- Each test class focuses on a single entity or function
- Test methods follow the pattern: `test_<feature>_<scenario>`

### 2. Fixtures

- Fixtures are defined in `conftest.py` for reusability
- Fixtures use descriptive names
- Fixtures are scoped appropriately (function, session)

### 3. Assertions

- Each test has clear, specific assertions
- Tests verify both success and failure cases
- Edge cases are tested

### 4. Mocking

- External dependencies are mocked (DynamoDB, Cognito)
- Mocks are configured to return realistic data
- Mock calls are verified when appropriate

### 5. Documentation

- All tests have docstrings explaining what they test
- Complex test logic is commented
- Fixtures are documented in README

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```bash
# Run tests with coverage
pytest tests/unit --cov=src/layers/common/python --cov-report=xml

# Generate coverage report
coverage report --fail-under=80
```

## Troubleshooting

### Import Errors

If you get import errors, ensure the Python path includes the common layer:

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/layers/common/python'))
```

### DynamoDB Errors

If DynamoDB tests fail, ensure `moto` is installed:

```bash
pip install moto[dynamodb]
```

### Cognito Errors

If Cognito tests fail, ensure environment variables are set:

```python
os.environ['USER_POOL_ID'] = 'test-pool'
os.environ['CLIENT_ID'] = 'test-client'
```

## Future Enhancements

- [ ] Integration tests with real AWS services
- [ ] Performance tests for DynamoDB queries
- [ ] Load testing for Lambda handlers
- [ ] Contract tests for API responses
- [ ] Mutation testing for better coverage
- [ ] Property-based testing with Hypothesis

## Contributing

When adding new tests:

1. Follow the existing test structure
2. Add fixtures to `conftest.py` if reusable
3. Use descriptive test names
4. Include docstrings
5. Test both success and failure cases
6. Update this README with new test categories

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Moto Documentation](https://docs.getmoto.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [AWS Lambda Testing](https://docs.aws.amazon.com/lambda/latest/dg/testing-functions.html)
