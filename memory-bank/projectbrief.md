# Project Brief: Multi-Player Fantasy Football/Tipping Competition Platform

## Overview
Multi-Player is a serverless full-stack application for creating and managing fantasy football/tipping competitions, similar to platforms run by major sports leagues (Premier League, AFL, etc.).

## Core Purpose
Enable users to:
- Create and join fantasy football/tipping leagues
- Compete against others in their league
- Track scores and standings in real-time
- View detailed statistics and leaderboards

## Technology Stack

### Backend
- **Runtime**: Python 3.12 on AWS Lambda
- **Framework**: AWS Lambda Powertools for Python
- **Database**: Amazon DynamoDB (single-table design)
- **API**: API Gateway v2 (HTTP API)
- **Authentication**: Amazon Cognito
- **IaC**: AWS SAM (Serverless Application Model)

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Hosting**: S3 + CloudFront

### Infrastructure
- **Frontend Hosting**: S3 (private) + CloudFront (CDN)
- **API Gateway**: HTTP API with Cognito authorization
- **Database**: DynamoDB with single-table design
- **Logging**: CloudWatch (via Lambda Powertools)
- **Tracing**: X-Ray (via Lambda Powertools)
- **Metrics**: CloudWatch Metrics (via Lambda Powertools)

## Key Features

### Authentication
- User sign-up and sign-in via Cognito
- JWT-based API authorization
- Secure token management

### League Management
- Create new leagues
- Join existing leagues
- View league details and members
- Track league standings

### User Features
- User profiles
- League membership tracking
- Personal statistics

## Architecture Decisions

### Single-Table DynamoDB Design
- **PK/SK Pattern**: Entity-type prefixed keys (e.g., `USER#<id>`, `LEAGUE#<id>`)
- **GSI1**: For inverted queries (e.g., find leagues by user)
- **Benefits**: Reduced costs, simplified queries, better data locality

### Lambda Powertools Usage
- **Logger**: Structured JSON logging with correlation IDs
- **Tracer**: X-Ray tracing for all functions
- **Metrics**: Custom CloudWatch metrics for business events
- **Event Handler**: Type-safe API routing

### Frontend Hosting Strategy
- **S3 + CloudFront**: Cost-effective, globally distributed
- **Origin Access Control (OAC)**: Modern security best practice
- **CloudFront Function**: SPA routing (404 → index.html)
- **Integrated with API Gateway**: Single CloudFront distribution for frontend + API

## Deployment Strategy
- **Environments**: dev, staging, prod
- **SAM Deployment**: `sam deploy --guided` for each environment
- **Frontend Deployment**: Build React → sync to S3 → invalidate CloudFront

## Security Considerations
- Cognito-protected API endpoints
- Private S3 bucket with OAC
- HTTPS-only CloudFront distribution
- Least-privilege IAM roles for Lambda functions
- Environment-specific Cognito domains

## Scalability
- **DynamoDB**: Pay-per-request billing (auto-scales)
- **Lambda**: Automatic scaling
- **CloudFront**: Global edge locations
- **API Gateway**: Managed scaling

## Cost Optimization
- Pay-per-request DynamoDB (no provisioned capacity)
- Lambda free tier (1M requests/month)
- CloudFront caching for static assets
- S3 versioning for rollback capability
