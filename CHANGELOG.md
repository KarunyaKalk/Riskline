# Changelog

All notable changes to the **Riskline** platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-24

### Initial Production Release (v1.0.0)

#### Day 1 — Foundation Stack
- Monorepo layout (`backend/`, `frontend/`, `infra/`, `docs/`).
- Docker Compose stack (`postgres` pgvector:16, `redis` 7-alpine, `backend` FastAPI, `frontend` React+Vite).
- Core multi-tenant database schema (`Organization`, `User`, `TeamMember`, `Change`, `RiskAnalysis`, `Note`, `ProjectProgress`, `ChatMessage`, `AuditLog`).
- Argon2id password hashing, JWT authentication, and RBAC primitives (`admin`, `engineer`, `business_ops`, `viewer`).

#### Day 2 — Core Domain Backend
- Full org-scoped CRUD for Team Roster, Notes Board (with tag filtering `#idea`, `#blocker`, `#decision`, `#question`), Project Progress, and Change Management.
- Org management & 48-hour teammate invite token generation/acceptance flow.
- Immutable audit logging on all mutation operations.
- Redis-backed rate limiting with in-memory sliding window fallback.

#### Day 3 — AI Core & Risk Engine
- Provider-agnostic `LLMClient` supporting OpenAI (`gpt-4o-mini`), Gemini (`gemini-1.5-flash`), and zero-cost Mock heuristic fallback with Pydantic structured output validation.
- `pgvector` RAG pipeline with sliding-window chunking and tenant-isolated vector search.
- PDF ingestion and text extraction service (`pypdf`).
- Async background pipeline for risk analysis execution.

#### Day 4 — Chat, Real-Time & Notifications
- Token-by-token streaming SSE chatbot endpoint (`POST /api/v1/chat/stream`) with `technical`, `business`, and `auto-detect` audience translation modes.
- Real-time tenant-isolated SSE event broadcaster (`GET /api/v1/events/stream`).
- High-risk alert notification engine (`risk_score >= 7.0`) with in-app, email, and Slack webhook delivery stubs.

#### Day 5 — Complete Frontend Application & Design System
- Mission Control design system in `index.css` (Deep Slate, Obsidian, Neon Cyan, Electric Violet).
- Full view build-out: Auth, Dashboard, Changes, Risk Analysis Detail, Chat Drawer, Notes Board, Team Roster, Org Settings, and Audit Logs.
- Vitest component test suite and Playwright E2E integration test spec.

#### Day 6 — Power BI Integration & Security Hardening
- API-Key authenticated tabular JSON export feed (`GET /api/v1/export/power-bi`) and Power BI setup documentation (`docs/power-bi-setup.md`).
- Security pass: tenant isolation audit, 1-hour single-use password reset flow, auth rate limiting, XSS sanitization, PDF magic byte validation, and strict CORS.
- Load performance benchmark script (`backend/scripts/benchmark_load.py`).

#### Day 7 — Production Scaffolding & Release
- Multi-stage production Dockerfiles and `docker-compose.prod.yml`.
- Structured JSON logging with `X-Request-ID` and `org_id` context binding.
- Sentry error tracking integration stubs.
- System usage metrics endpoint (`GET /api/v1/audit/metrics`).
- Complete documentation suite (`README.md`, `ARCHITECTURE.md`, `docs/deployment.md`, `CONTRIBUTING.md`, `docs/onboarding-guide.md`, `CHANGELOG.md`).
- Compliance baseline legal pages (`PrivacyPolicyPage`, `TermsOfServicePage`).
