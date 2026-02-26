# System Patterns: Multi-Player Architecture

## DynamoDB Single-Table Design

### Key Schema
```
PK (Partition Key): Entity type + ID (e.g., USER#<uuid>, LEAGUE#<uuid>)
SK (Sort Key): Entity subtype + ID (e.g., PROFILE, METADATA, MEMBER#<user-id>)
GSI1PK: Inverted query key (e.g., USER#<id> for league queries)
GSI1SK: Secondary sort key (e.g., LEAGUE#<id>)
```

### Entity Types
- **USER**: User profiles and settings
- **LEAGUE**: League metadata and configuration
- **LEAGUE_MEMBER**: League membership records
- **SCORE**: Individual scores and standings

### Access Patterns
1. Get user profile: `PK=USER#<id>, SK=PROFILE`
2. Get league details: `PK=LEAGUE#<id>, SK=METADATA`
3. Get league members: `PK=LEAGUE#<id>, SK begins_with MEMBER#`
4. Get user's leagues: `GSI1PK=USER#<id>, GSI1SK begins_with LEAGUE#`
5. Get league scores: `PK=LEAGUE#<id>, SK begins_with SCORE#`

## Lambda Function Architecture

### Pattern: Handler + Service Layer
```
app.py (Lambda Handler)
  ↓
service.py (Business Logic)
  ↓
repository.py (Data Access)
  ↓
DynamoDB
```

### Powertools Integration
- **Logger**: Injected at handler level with correlation IDs
- **Tracer**: Captures all AWS SDK calls
- **Metrics**: Custom metrics for business events
- **Event Handler**: Type-safe routing for HTTP events

### Error Handling
- Custom exceptions for domain errors
- Consistent error response format
- Proper HTTP status codes
- Detailed logging for debugging

## API Gateway Integration

### HTTP API (v2)
- Cognito authorizer for protected routes
- CORS configured for CloudFront domain
- Request/response transformation via Lambda
- Automatic OpenAPI documentation

### Authorization Flow
1. Client sends request with Authorization header
2. API Gateway validates JWT with Cognito
3. Claims injected into Lambda event
4. Lambda extracts user ID from claims
5. User-scoped queries executed

## Frontend Architecture

### Component Structure
```
src/
  ├── api/
  │   ├── client.ts (Axios instance)
  │   └── endpoints/ (API methods)
  ├── components/ (Reusable UI)
  ├── pages/ (Route-level components)
  ├── hooks/ (Custom React hooks)
  ├── types/ (TypeScript interfaces)
  └── utils/ (Helper functions)
```

### API Client Pattern
- Centralized Axios instance
- Request interceptor for auth tokens
- Response interceptor for error handling
- Type-safe API methods

### State Management
- React hooks for local state
- Context API for global state (future)
- Local storage for auth tokens

## Deployment Pipeline

### Backend (SAM)
1. `sam build` - Package Lambda functions and layers
2. `sam deploy --guided` - Deploy to AWS
3. CloudFormation creates/updates stack
4. Outputs: API endpoint, CloudFront domain, Cognito IDs

### Frontend
1. `npm run build` - Build React app with Vite
2. `scripts/deploy-frontend.sh` - Sync to S3
3. CloudFront cache invalidation
4. App available at CloudFront domain

## Security Patterns

### Authentication
- Cognito User Pool for user management
- JWT tokens for API authorization
- Refresh token rotation
- Secure token storage (localStorage)

### Authorization
- Cognito authorizer on API Gateway
- User ID extracted from JWT claims
- User-scoped DynamoDB queries
- Least-privilege IAM roles

### Data Protection
- DynamoDB encryption at rest
- HTTPS-only CloudFront
- S3 bucket private with OAC
- No sensitive data in logs

## Monitoring & Observability

### Logging
- Structured JSON logs via Powertools
- Correlation IDs for request tracing
- CloudWatch Logs for centralized logging
- Log retention policies

### Tracing
- X-Ray tracing via Powertools
- Service map visualization
- Performance insights
- Error tracking

### Metrics
- Custom CloudWatch metrics
- Cold start tracking
- Business metrics (signups, leagues created)
- API latency and error rates

## Caching Strategy

### CloudFront
- Static assets cached with long TTL
- API responses not cached (dynamic)
- Cache invalidation on deployment

### DynamoDB
- No application-level caching initially
- DynamoDB streams for future real-time features
- Consider ElastiCache for hot data (future)
