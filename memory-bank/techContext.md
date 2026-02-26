# Technical Context: Multi-Player

## Development Environment Setup

### Prerequisites
- Python 3.12
- Node.js 18+
- AWS CLI v2
- AWS SAM CLI
- Docker (for DynamoDB Local)
- Git

### Local Development

#### Backend
```bash
cd backend
pip install -r src/layers/common/requirements.txt
sam build
sam local start-api
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

#### DynamoDB Local
```bash
docker run -p 8000:8000 amazon/dynamodb-local
```

## Dependencies

### Backend (Python 3.12)
- `aws-lambda-powertools[all]==2.43.1` - Serverless best practices
- `boto3==1.34.0` - AWS SDK
- `pydantic==2.5.0` - Data validation
- `python-dateutil==2.8.2` - Date utilities

### Frontend (Node.js)
- `react@18.2.0` - UI framework
- `react-dom@18.2.0` - React DOM
- `react-router-dom@6.20.0` - Client routing
- `axios@1.6.0` - HTTP client
- `amazon-cognito-identity-js@6.2.0` - Cognito SDK
- `@aws-amplify/auth@6.0.0` - AWS Amplify Auth

### Dev Dependencies
- TypeScript 5.2.2
- Vite 5.0.0
- Vitest 1.0.0
- ESLint 8.53.0

## AWS Services Used

### Compute
- **AWS Lambda**: Function execution (Python 3.12)
- **API Gateway v2**: HTTP API with Cognito authorization

### Storage
- **DynamoDB**: NoSQL database (single-table design)
- **S3**: Frontend asset storage (private bucket)

### Authentication & Authorization
- **Cognito User Pool**: User management and authentication
- **Cognito Identity Pool**: Future mobile app support

### Content Delivery
- **CloudFront**: CDN for frontend and API
- **Origin Access Control (OAC)**: Secure S3 access

### Monitoring & Logging
- **CloudWatch Logs**: Application logs
- **CloudWatch Metrics**: Custom metrics
- **X-Ray**: Distributed tracing

### Infrastructure as Code
- **AWS SAM**: Serverless application model
- **CloudFormation**: Infrastructure provisioning

## Environment Configuration

### SAM Configuration (samconfig.toml)
- Stack names per environment (dev, staging, prod)
- S3 bucket for SAM artifacts
- Region: us-east-1 (default, customizable)
- Cognito domain prefix per environment

### Frontend Environment Variables (.env)
```
VITE_API_URL=<API Gateway endpoint>
VITE_COGNITO_REGION=us-east-1
VITE_COGNITO_USER_POOL_ID=<User Pool ID>
VITE_COGNITO_CLIENT_ID=<Client ID>
VITE_COGNITO_DOMAIN=<Cognito domain>
```

## Build & Deployment

### Backend Build
```bash
sam build
# Creates .aws-sam/ directory with packaged functions
```

### Backend Deployment
```bash
sam deploy --guided
# Interactive deployment with parameter prompts
# Creates CloudFormation stack
```

### Frontend Build
```bash
npm run build
# Outputs to dist/ directory
```

### Frontend Deployment
```bash
./scripts/deploy-frontend.sh
# Syncs dist/ to S3
# Invalidates CloudFront cache
```

## Testing Strategy

### Backend Testing
- Unit tests with pytest
- Integration tests with DynamoDB Local
- Mocking AWS services with moto

### Frontend Testing
- Component tests with Vitest
- Integration tests with React Testing Library
- E2E tests (future)

## Code Quality

### Backend
- Type hints with Python 3.12
- Pydantic for data validation
- Structured logging with Powertools
- Error handling with custom exceptions

### Frontend
- TypeScript strict mode
- ESLint for code quality
- Prettier for formatting
- React best practices

## Performance Considerations

### Lambda
- Memory: 512 MB (default, adjustable)
- Timeout: 30 seconds (default, adjustable)
- Cold start optimization via layers
- Provisioned concurrency (future)

### DynamoDB
- Pay-per-request billing
- On-demand scaling
- Single-table design for efficiency
- GSI for query flexibility

### CloudFront
- Static asset caching (long TTL)
- Compression enabled
- HTTP/2 and HTTP/3 support
- Edge locations worldwide

## Security Best Practices

### Secrets Management
- Cognito for user credentials
- SSM Parameter Store for config
- Secrets Manager for sensitive data
- No hardcoded secrets

### Network Security
- HTTPS-only CloudFront
- Private S3 bucket with OAC
- API Gateway authorization
- VPC (future, if needed)

### Data Protection
- DynamoDB encryption at rest
- HTTPS in transit
- No sensitive data in logs
- User-scoped queries

## Monitoring & Debugging

### CloudWatch
- Application logs with correlation IDs
- Custom metrics for business events
- Alarms for error rates and latency
- Log retention policies

### X-Ray
- Service map visualization
- Request tracing
- Performance analysis
- Error tracking

### Local Debugging
- SAM local invocation
- DynamoDB Local
- Browser DevTools for frontend
- VS Code debugger integration

## Continuous Integration/Deployment (Future)

### GitHub Actions (Planned)
- Lint and test on PR
- Build and deploy on merge to main
- Separate workflows for backend/frontend
- Environment-specific deployments
