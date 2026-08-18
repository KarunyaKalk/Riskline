# DevOps Change Intelligence & Risk Analysis Platform - Project Context

## Overview
A startup-ready DevOps Change Intelligence & Risk Analysis Platform built to improve cross-team transparency and efficiency for distributed/remote teams.
The platform ingests deployment/change data (pasted text or uploaded PDFs), uses an LLM + RAG pipeline to produce risk assessments, and presents technical summaries for engineers alongside plain-language summaries for business/ops stakeholders (with chatbot interaction). Includes a shared dashboard for risk overview, project progress, team roster, and shared notes/brainstorming.

## Multi-Tenancy Architecture Pattern
- **Day 1 Requirement**: Multi-tenant from the start.
- **Database Schema Pattern**: Every table containing team/org-specific data MUST include an `org_id` column as a foreign key referencing `organizations.id` (`ondelete="CASCADE"`).
- **SQLAlchemy Base Pattern**: Domain models inherit from `OrgScopedMixin` which enforces the `org_id` column and index.
- **API Security Pattern**: Route handlers use FastAPI dependencies (`get_current_user`, `get_current_org`) to extract `org_id` directly from authenticated JWT claims. Database queries must explicitly filter on `org_id == current_user.org_id`. Cross-organization data fetching is strictly forbidden.

## Architecture & Tech Stack Decisions (Confirmed)
- **Backend Framework**: FastAPI (Python 3.11+)
- **ORM & Migrations**: SQLAlchemy 2.x + Alembic
- **Database & Vector Store**: PostgreSQL 16 + `pgvector` extension (`pgvector/pgvector:pg16`)
- **Auth Standard**: JWT access (short-lived) & refresh tokens (long-lived) stored in `HttpOnly` cookies; Argon2id password hashing (`argon2-cffi`). Org-scoped role claims (`admin`, `member`).
- **Frontend**: React + Vite + React Router (Token handling via HttpOnly cookies with `credentials: include`)
- **LLM Integration**: Pluggable OpenAI / Gemini with Mock fallback mode
- **Containerization**: Docker & `docker-compose`
- **CI/CD**: GitHub Actions

## Current Status
- Day 1 Foundations in progress: Initialized root repository files, `PROJECT_CONTEXT.md`, database schema pattern.
