# 🇱🇰 Lanka Legal Analyst (LLA)

A state-of-the-art legal research assistant powered by **Agentic Retrieval-Augmented Generation (RAG)** for Sri Lankan Law.

## Overview

Lanka Legal Analyst (LLA) provides highly accurate, grounded, and citable information exclusively on **Sri Lankan Law**. Unlike traditional chatbots, LLA uses a system of specialized AI agents to plan, search, synthesize, and validate answers against official Acts, Ordinances, and Case Law, ensuring legal accuracy and minimizing hallucinations.

## Architecture

The system employs a multi-agent architecture:

- **Router Agent**: Analyzes query complexity and routes to appropriate agents
- **Planner Agent**: Decomposes complex queries into sequential sub-queries
- **Statutory Agent**: Retrieves exact sections from Acts and Ordinances
- **Case Law Agent**: Searches and summarizes legal precedents
- **Refiner Agent**: Validates citations and ensures legal grounding

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js 14 (React)
- **LLM**: Hybrid (GPT-4o, Claude 3.5, Local LLMs)
- **Vector DB**: Pinecone/Weaviate
- **Embeddings**: BGE-M3
- **Infrastructure**: AWS (ECS/EKS, RDS, S3)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- AWS CLI (for deployment)

### Local Development

1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Start services with Docker Compose:
   ```bash
   docker-compose up -d
   ```
4. Run backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn src.api.main:app --reload
   ```
5. Run frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Project Structure

See [DOC/architecture-plan.md](DOC/architecture-plan.md) for detailed architecture documentation.

## Documentation

- [Architecture Plan](DOC/architecture-plan.md)
- [Project Init](DOC/project-init.md)

## License

[Add your license here]

