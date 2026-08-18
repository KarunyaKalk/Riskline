# DevOps Change Intelligence & Risk Analysis Platform

A multi-tenant DevOps Change Intelligence & Risk Analysis Platform designed for distributed engineering teams. The platform ingests deployment/change data, performs automated risk assessment via an LLM + RAG pipeline, and generates audience-tailored technical and business summaries.

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2
- **Database & Vector Store**: PostgreSQL 16 + `pgvector`
- **Auth**: JWT (Access & Refresh Tokens) stored in HttpOnly Cookies, Argon2id password hashing
- **Frontend**: React (Vite), React Router
- **DevOps**: Docker, Docker Compose, GitHub Actions CI

## Quickstart (Local Development)

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (optional for local running outside Docker)
- Node.js 18+ (optional for local frontend dev)

### Running with Docker Compose

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd devops-risk-platform
   ```

2. Environment Configuration:
   ```bash
   cp backend/.env.example backend/.env
   ```

3. Spin up the Database & Backend:
   ```bash
   docker-compose up --build
   ```

4. Access the App:
   - Frontend: `http://localhost:5173`
   - Backend API Docs: `http://localhost:8000/docs`

## Architecture & Multi-Tenancy
Every table containing team data strictly references `organization_id`. Authorization dependencies extract the tenant scope from the JWT claim on every request to guarantee isolated data access.
