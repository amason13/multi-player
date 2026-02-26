# Testing Guide for Multi-Player Backend

## Quick Start

### 1. Install Test Dependencies

```bash
cd backend
pip install -r tests/requirements.txt
```

### 2. Run All Tests

```bash
pytest tests/unit -v
```

### 3. Run with Coverage

```bash
pytest tests/unit --cov=src/layers/common/python --cov-report=html
open htmlcov/index.html
```

## Test Files Overview

### `conftest.py` - Shared Fixtures

Contains all pytest fixtures used across test files:

- **Environment Setup**: `setup_test_env`
- **DynamoDB**: `dynamodb_table`, `dynamodb_table_wrapper`
- **User Models**: `user_id`, `valid_user_profile`, `valid_user_preferences`, etc.
- **Cognito**: `cognito_claims`, `lambda_event_with_auth`, `lambda_context`
- **Responses**: `success_response_200`, `error_response_400`, etc.
- **Mocks**: `mock_dynamodb_client`, `mock_cognito_client`, `mock_logger`
- **Sample Data**: `sample_dynamodb_item`, `sample_league_item`, etc.

### `test_models.py` - Entity Model Tests

Tests for Pydantic models and validation:

**Classes Tested:**
- `BaseEntity` - Core entity with DynamoDB keys
- `UserProfile` - User profile with validation
- `UserPreferences` - User preferences with enums
- `UserSettings` - Account settings with validation
- `UserStatistics` - Statistics with auto-calculations
- `UserProfileResponse` - API response model
- `UserStatisticsResponse` - API response model

**Test Coverage:**
- Model creation and initialization
- Field validation (email, name, country, language)
- Enum values
- Default values
- DynamoDB serialization
- DateTime handling
- Edge cases and error conditions

**Example Test:**
```python
def test_user_profile_creation(self, user_id):
    """Test creating a UserProfile instance."""
    profile = UserProfile(
        pk=f'USER#{user_id}',
        sk='PROFILE',
        user_id=user_id,
        email='test@example.com',
        name='Test User',
        entity_type='USER'
    )
    assert profile.user_id == user_id
    assert profile.email == 'test@example.com'
```

### `test_repositories.py` - Repository Tests

Tests for DynamoDB operations:

**Classes Tested:**
- `DynamoDBTable` - Low-level DynamoDB wrapper
- `UserRepository` - User-specific operations

**Test Coverage:**
- CRUD operations (Create, Read, Update, Delete)
- Query operations (by PK, with SK prefix, by GSI)
- Batch operations
- User status management
- Login tracking
- Error handling

**Example Test:**
```python
@mock_dynamodb
def test_get_profile_success(self, dynamodb_table_wrapper, user_id, valid_user_profile):
    """Test getting a user profile."""
    repo = UserRepository(dynamodb_table_wrapper)
    repo.create_profile(valid_user_profile)
    
    result = repo.get_profile(user_id)
    
    assert result is not None
    assert result['user_id'] == user_id
```

### `test_lambda_handlers.py` - Lambda Handler Tests

Tests for Lambda function handlers:

**Handlers Tested:**
- User Profile Handler (`GET /api/users/profile`)
- Sign Up Handler (`POST /api/auth/signup`)
- Sign In Handler (`POST /api/auth/signin`)
- Create League Handler (`POST /api/leagues`)
- Get League Handler (`GET /api/leagues/{leagueId}`)
- List Leagues Handler (`GET /api/leagues`)

**Test Coverage:**
- Success scenarios
- Missing required fields
- Invalid input
- Authentication/Authorization
- Error responses
- Response formatting

**Example Test:**
```python
@mock_dynamodb
def test_get_profile_success(self, lambda_event_with_auth, lambda_context, user_id):
    """Test successfully getting user profile."""
    # Setup DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(...)
    
    # Put test profile
    table.put_item(Item={...})
    
    # Call handler
    response = lambda_handler(lambda_event_with_auth, lambda_context)
    
    assert response['statusCode'] == 200
```

### `test_exceptions_and_responses.py` - Exception & Response Tests

Tests for error handling and response formatting:

**Classes Tested:**
- `MultiPlayerException` - Base exception
- `ValidationError` - 400 errors
- `NotFoundError` - 404 errors
- `UnauthorizedError` - 401 errors
- `ConflictError` - 409 errors
- `success_response()` - Success response helper
- `error_response()` - Error response helper

**Test Coverage:**
- Exception creation and attributes
- Exception inheritance
- Response formatting
- CORS headers
- JSON serialization
- Exception to response mapping

**Example Test:**
```python
def test_validation_error_creation(self):
    """Test creating a ValidationError."""
    exc = ValidationError('Invalid input')
    assert exc.message == 'Invalid input'
    assert exc.status_code == 400
    assert exc.error_code == 'VALIDATION_ERROR'
```

## Running Specific Tests

### Run All Tests in a File

```bash
pytest tests/unit/test_models.py -v
```

### Run a Specific Test Class

```bash
pytest tests/unit/test_models.py::TestUserProfile -v
```

### Run a Specific Test Method

```bash
pytest tests/unit/test_models.py::TestUserProfile::test_user_profile_creation -v
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

### Run Tests with Specific Pattern

```bash
# Run all tests with "profile" in the name
pytest tests/unit -k profile -v

# Run all tests with "success" in the name
pytest tests/unit -k success -v
```

## Test Execution Examples

### Example 1: Test User Profile Creation

```bash
pytest tests/unit/test_models.py::TestUserProfile::test_user_profile_creation -v
```

Output:
```
test_models.py::TestUserProfile::test_user_profile_creation PASSED
```

### Example 2: Test Repository CRUD Operations

```bash
pytest tests/unit/test_repositories.py::TestUserRepository -v
```

Output:
```
test_repositories.py::TestUserRepository::test_get_profile_success PASSED
test_repositories.py::TestUserRepository::test_create_profile_success PASSED
test_repositories.py::TestUserRepository::test_update_profile_success PASSED
test_repositories.py::TestUserRepository::test_delete_user_soft_delete PASSED
```

### Example 3: Test Lambda Handler with Coverage

```bash
pytest tests/unit/test_lambda_handlers.py::TestUserProfileHandler -v --cov=src/layers/common/python
```

## Debugging Tests

### Run with Verbose Output

```bash
pytest tests/unit -vv
```

### Run with Print Statements

```bash
pytest tests/unit -s
```

### Run with Detailed Traceback

```bash
pytest tests/unit --tb=long
```

### Run with PDB Debugger

```bash
pytest tests/unit --pdb
```

### Run with Breakpoint

Add to test:
```python
def test_example():
    breakpoint()  # Execution will pause here
    # ... rest of test
```

## Coverage Reports

### Generate HTML Coverage Report

```bash
pytest tests/unit --cov=src/layers/common/python --cov-report=html
open htmlcov/index.html
```

### Generate Terminal Coverage Report

```bash
pytest tests/unit --cov=src/layers/common/python --cov-report=term-missing
```

### Check Coverage Threshold

```bash
pytest tests/unit --cov=src/layers/common/python --cov-fail-under=80
```

## Common Issues and Solutions

### Issue: Import Errors

**Problem:** `ModuleNotFoundError: No module named 'models'`

**Solution:** Ensure `conftest.py` adds the common layer to sys.path:
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/layers/common/python'))
```

### Issue: DynamoDB Errors

**Problem:** `botocore.exceptions.ClientError: An error occurred`

**Solution:** Ensure `moto` is installed and decorator is applied:
```bash
pip install moto[dynamodb]
```

```python
@mock_dynamodb
def test_example():
    # Test code
```

### Issue: Cognito Mocking Errors

**Problem:** `AttributeError: 'MagicMock' object has no attribute 'exceptions'`

**Solution:** Use proper mock setup:
```python
with patch('boto3.client') as mock_client:
    mock_cognito = MagicMock()
    mock_client.return_value = mock_cognito
    # Configure mock
```

### Issue: Fixture Not Found

**Problem:** `fixture 'user_id' not found`

**Solution:** Ensure `conftest.py` is in the tests directory and fixtures are defined.

## Best Practices

### 1. Use Fixtures for Reusable Data

```python
def test_example(self, valid_user_profile):
    # Use fixture instead of creating data in test
    assert valid_user_profile.email == 'test@example.com'
```

### 2. Test Both Success and Failure Cases

```python
def test_success(self):
    # Test happy path
    assert result == expected

def test_failure(self):
    # Test error case
    with pytest.raises(ValidationError):
        # Code that should raise
```

### 3. Use Descriptive Test Names

```python
# Good
def test_user_profile_creation_with_valid_data(self):
    pass

# Bad
def test_profile(self):
    pass
```

### 4. Keep Tests Focused

```python
# Good - Tests one thing
def test_user_profile_email_validation(self):
    with pytest.raises(ValidationError):
        UserProfile(..., email='invalid')

# Bad - Tests multiple things
def test_user_profile(self):
    # Create profile
    # Validate email
    # Validate name
    # Check DynamoDB conversion
```

### 5. Use Mocking for External Dependencies

```python
# Good - Mocks DynamoDB
@mock_dynamodb
def test_repository_operation(self):
    # Test with mocked DynamoDB

# Bad - Tries to use real DynamoDB
def test_repository_operation(self):
    # Test with real AWS (slow, unreliable)
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install -r backend/tests/requirements.txt
      - run: pytest backend/tests/unit --cov=backend/src/layers/common/python
```

## Performance Tips

### Run Tests in Parallel

```bash
pip install pytest-xdist
pytest tests/unit -n auto
```

### Run Only Failed Tests

```bash
pytest tests/unit --lf
```

### Run Only Recently Changed Tests

```bash
pytest tests/unit --ff
```

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Moto Documentation](https://docs.getmoto.org/)
- [Pydantic Testing](https://docs.pydantic.dev/latest/concepts/models/#model-validation)
- [AWS Lambda Testing Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/testing-functions.html)
