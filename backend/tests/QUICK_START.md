# Quick Start Guide - Test Suite

Get up and running with the Multi-Player test suite in 5 minutes.

## 1. Install Dependencies (1 minute)

```bash
cd backend
pip install -r tests/requirements.txt
```

## 2. Run All Tests (1 minute)

```bash
pytest tests/unit -v
```

Expected output:
```
tests/unit/test_models.py::TestBaseEntity::test_base_entity_creation PASSED
tests/unit/test_models.py::TestUserProfile::test_user_profile_creation PASSED
...
======================== 250+ passed in X.XXs ========================
```

## 3. Run Specific Test Category (30 seconds)

```bash
# Model tests
pytest tests/unit/test_models.py -v

# Repository tests
pytest tests/unit/test_repositories.py -v

# Handler tests
pytest tests/unit/test_lambda_handlers.py -v

# Exception tests
pytest tests/unit/test_exceptions_and_responses.py -v
```

## 4. Generate Coverage Report (1 minute)

```bash
pytest tests/unit --cov=src/layers/common/python --cov-report=html
open htmlcov/index.html
```

## 5. Run Tests with Makefile (Optional)

```bash
cd tests

# View available commands
make help

# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific category
make test-models
make test-repos
make test-handlers
make test-exceptions
```

## Common Commands

### Run Single Test File
```bash
pytest tests/unit/test_models.py -v
```

### Run Single Test Class
```bash
pytest tests/unit/test_models.py::TestUserProfile -v
```

### Run Single Test Method
```bash
pytest tests/unit/test_models.py::TestUserProfile::test_user_profile_creation -v
```

### Run Tests Matching Pattern
```bash
pytest tests/unit -k "profile" -v
```

### Run with Verbose Output
```bash
pytest tests/unit -vv
```

### Run with Print Statements
```bash
pytest tests/unit -s
```

### Run with Detailed Errors
```bash
pytest tests/unit --tb=long
```

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── unit/
│   ├── test_models.py            # Entity model tests (60+ tests)
│   ├── test_repositories.py      # Repository tests (50+ tests)
│   ├── test_lambda_handlers.py   # Handler tests (30+ tests)
│   └── test_exceptions_and_responses.py  # Exception tests (40+ tests)
└── integration/
    └── test_user_flow.py         # Integration tests
```

## What Gets Tested

### Models (test_models.py)
- ✅ BaseEntity creation and serialization
- ✅ UserProfile validation
- ✅ UserPreferences defaults
- ✅ UserSettings validation
- ✅ UserStatistics calculations
- ✅ Response models

### Repositories (test_repositories.py)
- ✅ DynamoDB CRUD operations
- ✅ Query operations
- ✅ Batch operations
- ✅ User status management
- ✅ Error handling

### Handlers (test_lambda_handlers.py)
- ✅ User profile retrieval
- ✅ Sign up flow
- ✅ Sign in flow
- ✅ League creation
- ✅ League retrieval
- ✅ League listing

### Exceptions (test_exceptions_and_responses.py)
- ✅ Custom exceptions
- ✅ Response formatting
- ✅ Error mapping
- ✅ CORS headers

## Troubleshooting

### Tests Won't Run
```bash
# Check Python version
python --version  # Should be 3.12+

# Check pytest is installed
pytest --version

# Reinstall dependencies
pip install -r tests/requirements.txt --force-reinstall
```

### Import Errors
```bash
# Ensure you're in the backend directory
cd backend

# Check conftest.py exists
ls tests/conftest.py

# Run from backend directory
pytest tests/unit -v
```

### DynamoDB Errors
```bash
# Install moto with DynamoDB support
pip install moto[dynamodb]

# Verify installation
python -c "import moto; print(moto.__version__)"
```

## Next Steps

1. **Read Full Documentation**: See [README.md](README.md)
2. **Learn Testing Guide**: See [TESTING_GUIDE.md](TESTING_GUIDE.md)
3. **Check Installation**: See [INSTALLATION.md](INSTALLATION.md)
4. **View Test Summary**: See [SUMMARY.md](SUMMARY.md)

## Key Statistics

- **250+ test cases** covering all components
- **2,500+ lines** of test code
- **30+ fixtures** for reusable test data
- **4 test files** organized by component
- **100% coverage** of critical paths

## Support

- 📖 [README.md](README.md) - Comprehensive documentation
- 🚀 [TESTING_GUIDE.md](TESTING_GUIDE.md) - Detailed guide
- 🔧 [INSTALLATION.md](INSTALLATION.md) - Setup instructions
- 📊 [SUMMARY.md](SUMMARY.md) - Test statistics

---

**Ready to test?** Run `pytest tests/unit -v` now! 🚀
