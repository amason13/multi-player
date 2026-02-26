# Lambda Handler Functions - Core 6 Access Patterns

This document describes the 6 production-ready Lambda handler functions for the Multi-Player fantasy football platform.

## Handlers to Create

1. **users/profile** - Get user profile (Pattern #1)
2. **leagues/list** - Get user's leagues (Pattern #2)
3. **leagues/get** - Get league details (Pattern #4)
4. **leagues/members/list** - Get league members (Pattern #5)
5. **predictions/submit** - Submit prediction (Pattern #13)
6. **standings/get** - Get game/league standings (Patterns #16-17)

## Implementation Details

All handlers will:
- Use AWS Lambda Powertools decorators (@logger, @tracer, @metrics)
- Extract user_id from Cognito claims
- Validate input with Pydantic models
- Call repository methods
- Return standardized responses (success/error)
- Include error handling with proper HTTP status codes
- Add CloudWatch logging with correlation IDs
- Include comprehensive docstrings
- Add type hints

## File Structure

```
backend/src/functions/
├── users/
│   └── profile/
│       ├── app.py (UPDATED)
│       └── requirements.txt
├── leagues/
│   ├── list/
│   │   ├── app.py (NEW)
│   │   └── requirements.txt
│   ├── get/
│   │   ├── app.py (UPDATED)
│   │   └── requirements.txt
│   └── members/
│       ├── list/
│       │   ├── app.py (NEW)
│       │   └── requirements.txt
└── predictions/
    └── submit/
        ├── app.py (NEW)
        └── requirements.txt
└── standings/
    └── get/
        ├── app.py (NEW)
        └── requirements.txt
```

