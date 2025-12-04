# Lanka Legal Analyst (LLA): World-Class System Architecture Plan

## System Architecture Overview

The LLA system will be built as a **microservices-based, cloud-native architecture** following clean architecture principles, ensuring scalability, maintainability, and production-grade reliability.

### High-Level Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Web Client    │────▶│   API Gateway    │────▶│  Orchestrator   │
│   (React/Next)  │     │   (FastAPI)      │     │   Service       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
        ┌────────────────────────────────────────────────┼──────────────┐
        │                                                  │              │
        ▼                                                  ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Router Agent │  │ Planner Agent│  │Statutory Agent│  │Case Law Agent│
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
        │                                                  │
        └──────────────────┬──────────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Refiner Agent   │
                  └─────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Vector DB    │  │ LLM Service  │  │ Data Pipeline│
│ (Pinecone/   │  │ (Hybrid)     │  │ Service      │
│  Weaviate)   │  └──────────────┘  └──────────────┘
└──────────────┘
```

## Project Structure

```
SATHYA_AI/
├── backend/
│   ├── src/
│   │   ├── api/                    # FastAPI application
│   │   │   ├── routes/             # API endpoints
│   │   │   ├── middleware/         # Auth, rate limiting, logging
│   │   │   └── dependencies/       # Dependency injection
│   │   ├── core/                   # Core business logic
│   │   │   ├── agents/             # All 5 agent implementations
│   │   │   │   ├── router.py
│   │   │   │   ├── planner.py
│   │   │   │   ├── statutory.py
│   │   │   │   ├── case_law.py
│   │   │   │   └── refiner.py
│   │   │   ├── orchestrator.py     # Main orchestration logic
│   │   │   ├── prompts/            # System prompts for agents
│   │   │   └── config/              # Configuration management
│   │   ├── services/               # Service layer
│   │   │   ├── llm_service.py      # Hybrid LLM abstraction
│   │   │   ├── vector_service.py   # Vector DB operations
│   │   │   ├── embedding_service.py # Embedding generation
│   │   │   └── citation_service.py # Citation formatting
│   │   ├── data/                    # Data access layer
│   │   │   ├── repositories/       # Data repositories
│   │   │   └── models/             # Data models
│   │   └── utils/                   # Utilities
│   ├── tests/                       # Comprehensive test suite
│   ├── alembic/                     # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── data-pipeline/
│   ├── src/
│   │   ├── scrapers/               # Legal document scrapers
│   │   │   ├── gazette_scraper.py
│   │   │   ├── acts_scraper.py
│   │   │   └── case_law_scraper.py
│   │   ├── processors/             # Document processing
│   │   │   ├── pdf_parser.py
│   │   │   ├── chunker.py          # Legal structure-aware chunking
│   │   │   └── metadata_extractor.py
│   │   ├── indexers/               # Vector indexing
│   │   │   └── vector_indexer.py
│   │   └── schedulers/             # Automated ingestion
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/             # React components
│   │   ├── pages/                  # Next.js pages
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── services/               # API client
│   │   └── styles/                 # Styling
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── infrastructure/
│   ├── terraform/                  # Infrastructure as Code
│   │   ├── aws/                    # AWS resources
│   │   │   ├── ecs.tf
│   │   │   ├── rds.tf
│   │   │   ├── s3.tf
│   │   │   └── vpc.tf
│   │   └── modules/                # Reusable modules
│   ├── kubernetes/                 # K8s manifests
│   │   ├── deployments/
│   │   ├── services/
│   │   └── configmaps/
│   └── docker-compose.yml          # Local development
├── monitoring/
│   ├── prometheus/                 # Metrics collection
│   ├── grafana/                    # Dashboards
│   └── loki/                       # Log aggregation
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── deployment.md
├── .github/
│   └── workflows/                  # CI/CD pipelines
├── .env.example
├── README.md
└── pyproject.toml                  # Python project config
```

## Core Components

### 1. Agent Framework (`backend/src/core/agents/`)

Each agent will be implemented as a **LangGraph/LangChain agent** with:

- **Router Agent**: Classification model (simple vs complex query routing)
- **Planner Agent**: Multi-step query decomposition using ReAct pattern
- **Statutory Agent**: Specialized retrieval for Acts and Ordinances
- **Case Law Agent**: Precedent search with temporal awareness
- **Refiner Agent**: Fact-checking and citation validation

### 2. Hybrid LLM Service (`backend/src/services/llm_service.py`)

Abstract LLM interface supporting:

- **Cloud LLMs**: OpenAI GPT-4o, Anthropic Claude 3.5 (for complex queries)
- **Local LLMs**: Ollama/Llama 3, Mistral (for simple queries)
- **Intelligent routing**: Route based on query complexity
- **Fallback mechanism**: Automatic fallback to cloud if local fails
- **Cost optimization**: Token usage tracking and optimization

### 3. Vector Database & Embeddings

- **Primary**: Pinecone or Weaviate (cloud-managed, scalable)
- **Fallback**: ChromaDB (local development)
- **Embedding Model**: BGE-M3 or legal-specialized model (e.g., Legal-BERT)
- **Metadata Indexing**: Hierarchical structure (Act → Part → Chapter → Section)
- **Hybrid Search**: Semantic + keyword search for precision

### 4. Data Pipeline (`data-pipeline/`)

Automated ingestion pipeline:

- **Scrapers**: Government Gazette, legal databases
- **Processing**: PDF parsing, OCR, structure extraction
- **Chunking**: Legal structure-aware (preserve section boundaries)
- **Indexing**: Incremental updates, version control
- **Scheduling**: Automated daily/weekly ingestion

### 5. API Layer (`backend/src/api/`)

**FastAPI** REST API with:

- **OpenAPI/Swagger** documentation
- **Authentication**: JWT-based auth
- **Rate limiting**: Per-user and per-IP limits
- **Request/Response models**: Pydantic validation
- **Error handling**: Structured error responses
- **Caching**: Redis for frequent queries
- **WebSocket**: For streaming responses

### 6. Web Application (`frontend/`)

**Next.js 14** with:

- **Modern UI**: Tailwind CSS, shadcn/ui components
- **Chat Interface**: Real-time conversation UI
- **Citation Display**: Interactive citation links
- **Search**: Advanced query builder
- **Responsive Design**: Mobile-first approach

## Infrastructure & DevOps

### Cloud Infrastructure (AWS)

- **Compute**: ECS Fargate or EKS for container orchestration
- **Database**: PostgreSQL (RDS) for metadata, Redis (ElastiCache) for caching
- **Storage**: S3 for document storage, vector DB (Pinecone/Weaviate)
- **Networking**: VPC, ALB, CloudFront CDN
- **Monitoring**: CloudWatch, X-Ray for tracing
- **Secrets**: AWS Secrets Manager

### CI/CD Pipeline

- **GitHub Actions** workflows:
  - Unit/integration tests
  - Code quality checks (black, pylint, mypy)
  - Security scanning
  - Docker image building
  - Automated deployment to staging/production

### Observability

- **Metrics**: Prometheus + Grafana
- **Logging**: Structured logging (JSON) → CloudWatch/ELK
- **Tracing**: OpenTelemetry for distributed tracing
- **Alerting**: PagerDuty/CloudWatch Alarms

## Security & Compliance

- **Authentication**: OAuth2/JWT with refresh tokens
- **Authorization**: Role-based access control (RBAC)
- **Data Encryption**: At-rest (S3 encryption) and in-transit (TLS)
- **API Security**: Rate limiting, input validation, SQL injection prevention
- **Audit Logging**: All queries and responses logged
- **Compliance**: GDPR-ready, data retention policies

## Testing Strategy

- **Unit Tests**: pytest for all agents and services
- **Integration Tests**: Test agent workflows end-to-end
- **API Tests**: FastAPI TestClient
- **Load Testing**: Locust for performance testing
- **Accuracy Testing**: Legal expert validation dataset

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)

- Project structure setup
- Basic FastAPI skeleton
- Vector DB setup (Pinecone/Weaviate)
- Simple RAG implementation
- Basic web UI

### Phase 2: Agent Framework (Weeks 3-4)

- Implement all 5 agents
- Orchestrator logic
- Hybrid LLM service
- Agent testing

### Phase 3: Data Pipeline (Weeks 5-6)

- Document scrapers
- Legal structure-aware chunking
- Vector indexing pipeline
- Initial data ingestion

### Phase 4: Production Readiness (Weeks 7-8)

- Infrastructure setup (Terraform)
- CI/CD pipeline
- Monitoring and logging
- Security hardening
- Performance optimization

### Phase 5: Enhancement (Ongoing)

- Multilingual support
- Advanced features (hierarchical indexing, real-time updates)
- Mobile app (if needed)

## Key Design Decisions

1. **Microservices**: Separate services for scalability and independent deployment
2. **Clean Architecture**: Separation of concerns, testability
3. **Hybrid LLM**: Cost optimization while maintaining quality
4. **Cloud-Native**: Leverage managed services for reliability
5. **Legal Structure Preservation**: Custom chunking maintains legal context
6. **Citation-First Design**: Every response must be citable and verifiable

