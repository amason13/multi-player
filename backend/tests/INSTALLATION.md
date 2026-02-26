# Test Suite Installation and Setup

## Prerequisites

- Python 3.12+
- pip (Python package manager)
- Git (for version control)

## Installation Steps

### 1. Navigate to Backend Directory

```bash
cd backend
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Test Dependencies

```bash
pip install -r tests/requirements.txt
```

This installs:
- **pytest** and plugins (pytest-cov, pytest-mock, pytest-asyncio)
- **moto** for AWS service mocking
- **boto3** for AWS SDK
- **pydantic** for data validation
- **aws-lambda-powertools** for Lambda utilities
- **Code quality tools** (black, flake8, mypy, coverage)

### 4. Verify Installation

```bash
# Check pytest is installed
pytest --version

# Check moto is installed
python -c "import moto; print(moto.__version__)"

# Check pydantic is installed
python -c "import pydantic; print(pydantic.__version__)"
```

## Running Tests

### Run All Tests

```bash
pytest tests/unit -v
```

### Run with Coverage Report

```bash
pytest tests/unit --cov=src/layers/common/python --cov-report=html
open htmlcov/index.html
```

### Run Specific Test File

```bash
pytest tests/unit/test_models.py -v
```

### Run Specific Test Class

```bash
pytest tests/unit/test_models.py::TestUserProfile -v
```

### Run Specific Test Method

```bash
pytest tests/unit/test_models.py::TestUserProfile::test_user_profile_creation -v
```

## Troubleshooting Installation

### Issue: `ModuleNotFoundError: No module named 'pytest'`

**Solution:**
```bash
pip install pytest==7.4.3
```

### Issue: `ModuleNotFoundError: No module named 'moto'`

**Solution:**
```bash
pip install moto[dynamodb]==4.2.9
```

### Issue: `ModuleNotFoundError: No module named 'pydantic'`

**Solution:**
```bash
pip install pydantic==2.5.0
```

### Issue: `ModuleNotFoundError: No module named 'boto3'`

**Solution:**
```bash
pip install boto3==1.34.0
```

### Issue: Virtual Environment Not Activated

**Solution:**
```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# Verify activation (should show (venv) in prompt)
```

### Issue: Permission Denied on macOS/Linux

**Solution:**
```bash
chmod +x venv/bin/activate
source venv/bin/activate
```

## Development Setup

### Install Development Tools

```bash
# Install code quality tools
pip install black==23.12.0 flake8==6.1.0 mypy==1.7.1 isort==5.13.2
```

### Format Code with Black

```bash
black tests/
```

### Check Code Quality with Flake8

```bash
flake8 tests/
```

### Type Check with MyPy

```bash
mypy tests/
```

### Sort Imports with isort

```bash
isort tests/
```

## IDE Setup

### VS Code

1. Install Python extension
2. Select Python interpreter:
   - Command Palette: `Python: Select Interpreter`
   - Choose `./venv/bin/python`
3. Install pytest extension
4. Configure pytest in `.vscode/settings.json`:

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests"
  ]
}
```

### PyCharm

1. Open project settings
2. Go to Project > Python Interpreter
3. Click gear icon > Add
4. Select Existing Environment
5. Navigate to `venv/bin/python`
6. Click OK

## Continuous Integration Setup

### GitHub Actions

Create `.github/workflows/tests.yml`:

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

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
test:
  image: python:3.12
  script:
    - pip install -r backend/tests/requirements.txt
    - pytest backend/tests/unit --cov=backend/src/layers/common/python
```

## Docker Setup

Create `Dockerfile.test`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY backend/tests/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/src ./src
COPY backend/tests ./tests

CMD ["pytest", "tests/unit", "-v"]
```

Build and run:

```bash
docker build -f Dockerfile.test -t multi-player-tests .
docker run multi-player-tests
```

## Environment Variables

Set environment variables for tests:

```bash
# macOS/Linux
export TABLE_NAME=test-table
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=testing
export AWS_SECRET_ACCESS_KEY=testing

# Windows
set TABLE_NAME=test-table
set AWS_DEFAULT_REGION=us-east-1
set AWS_ACCESS_KEY_ID=testing
set AWS_SECRET_ACCESS_KEY=testing
```

Or create `.env` file:

```
TABLE_NAME=test-table
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=testing
AWS_SECRET_ACCESS_KEY=testing
```

## Uninstalling

### Remove Virtual Environment

```bash
# macOS/Linux
rm -rf venv

# Windows
rmdir /s venv
```

### Remove Test Dependencies

```bash
pip uninstall -r tests/requirements.txt -y
```

## Next Steps

1. Read [README.md](README.md) for comprehensive documentation
2. Read [TESTING_GUIDE.md](TESTING_GUIDE.md) for quick start
3. Run tests: `pytest tests/unit -v`
4. Check coverage: `pytest tests/unit --cov=src/layers/common/python --cov-report=html`

## Support

For issues or questions:
1. Check [TESTING_GUIDE.md](TESTING_GUIDE.md) troubleshooting section
2. Review test files for examples
3. Check pytest documentation: https://docs.pytest.org/
4. Check moto documentation: https://docs.getmoto.org/
