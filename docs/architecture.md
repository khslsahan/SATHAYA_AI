# Architecture Documentation

See [DOC/architecture-plan.md](../DOC/architecture-plan.md) for the complete architecture plan.

## Quick Reference

### System Components

1. **Backend**: FastAPI application with agent orchestration
2. **Frontend**: Next.js web application
3. **Data Pipeline**: Document ingestion and indexing
4. **Infrastructure**: AWS cloud resources

### Agent Flow

1. Router Agent → Classifies query
2. Planner Agent → Decomposes complex queries (if needed)
3. Statutory/Case Law Agents → Retrieve relevant documents
4. Refiner Agent → Validates and refines answer

