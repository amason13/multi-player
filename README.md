# Multi-Player: Fantasy Football/Tipping Competition Platform

A serverless full-stack application for creating and managing fantasy football/tipping competitions, built with AWS serverless technologies.

## 🏗️ Architecture

- **Backend**: AWS Lambda (Python 3.12) with Lambda Powertools, API Gateway, DynamoDB (single-table design)
- **Frontend**: React 18 + TypeScript with Vite
- **Authentication**: Amazon Cognito
- **Hosting**: S3 + CloudFront (frontend), API Gateway (backend)
- **IaC**: AWS SAM (Serverless Application Model)

## 📁 Project Structure

```
multi-player/
├── memory-bank/              # Project documentation & context
├── frontend/                 # React + TypeScript application
│   ├── src/
│   │   ├── api/             # API client layer
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Route-level pages
│   │   ├── hooks/           # Custom React hooks
│   │   ├── types/           # TypeScript interfaces
│   │   └── utils/           # Helper functions
│   └── package.json
├── backend/                  # SAM application
│   ├── template.yaml        # SAM infrastructure template
│   ├── samconfig.toml       # SAM deployment config
│   └── src/
│       ├── functions/       # Lambda function handlers
│       ├── layers/          # Shared Lambda layer (Powertools, models, repo)
│       └── tests/           # Unit & integration tests
├── scripts/                  # Build & deployment scripts
├── docs/                     # Architecture & decision records
└── .gitignore
```

## 🚀 Getting Started

### Prerequisites

- Python 3.12
- Node.js 18+
- AWS CLI configured
- AWS SAM CLI
- Docker (for local DynamoDB)

### Local Development

1. **Install dependencies**:
   ```bash
   # Backend
   cd backend
   pip install -r src/layers/common/requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

2. **Start DynamoDB Local** (optional):
   ```bash
   docker run -p 8000:8000 amazon/dynamodb-local
   ```

3. **Run SAM locally**:
   ```bash
   cd backend
   sam build
   sam local start-api
   ```

4. **Run frontend dev server**:
   ```bash
   cd frontend
   npm run dev
   ```

### Deployment

```bash
# Backend
cd backend
sam build
sam deploy --guided

# Frontend
cd frontend
npm run build
./scripts/deploy-frontend.sh
```

## 🎮 Features

- **User Authentication**: Cognito-protected API
- **League Management**: Create and join leagues
- **Competition Tracking**: Track scores and standings
- **Leaderboards**: Real-time leaderboard updates
- **Statistics**: Detailed player and league statistics

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Vite, React Router |
| **Backend** | Python 3.12, Lambda Powertools, Boto3 |
| **Database** | DynamoDB (single-table design) |
| **Auth** | Amazon Cognito |
| **API** | API Gateway v2 (HTTP API) |
| **Hosting** | S3 + CloudFront |
| **IaC** | AWS SAM |
| **Testing** | pytest, Vitest |

## 📚 Documentation

- [Architecture Decision Records](./docs/adr/)
- [Memory Bank](./memory-bank/)

## 📝 License

MIT
