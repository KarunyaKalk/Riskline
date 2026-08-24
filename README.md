# Riskline — Multi-Tenant DevOps Change Intelligence & AI Risk Assessment Platform

[![CI Pipeline](https://github.com/KarunyaKalk/Riskline/actions/workflows/ci.yml/badge.svg)](https.github.com/KarunyaKalk/Riskline/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release: v1.0.0](https://img.shields.io/badge/Release-v1.0.0-emerald.svg)](CHANGELOG.md)

**Riskline** is a production-ready, multi-tenant "Mission Control" platform designed for engineering and business teams to evaluate deployment changes, predict architectural risk, collaborate on incident notes, stream live updates, and export analytics directly to Power BI.

---

## ⚡ Key Features

- **Multi-Tenant Scoping**: Hardened database-level isolation (`org_id` mixin) across all relational and vector search queries.
- **AI Risk Assessment Engine**: Grounded RAG analysis supporting OpenAI (`gpt-4o-mini`), Gemini (`gemini-1.5-flash`), and a zero-cost heuristic fallback engine for offline/CI execution. Accepts raw text or PDF change specifications.
- **Real-Time Event Broadcasting**: Server-Sent Events (SSE) stream live deployment changes, high-risk alerts, and brainstorm board notes across team contexts.
- **Streaming Chatbot with Audience Modes**: Token-by-token SSE streaming AI assistant supporting `Technical` (SRE), `Business` (Exec), and `Auto-Detect` audience translation modes.
- **Power BI Integration**: API-Key authenticated read-only JSON export feed (`GET /api/v1/export/power-bi`) for Power BI Desktop executive dashboards.
- **Security & Auditability**: Single-use password reset tokens, Argon2id password hashing, Redis-backed rate limiting, role-based access control (RBAC), and immutable audit logs.

---

## 🚀 Quickstart (Local Development)

Launch the full stack locally with PostgreSQL (pgvector), Redis, FastAPI backend, and React frontend:

```bash
# 1. Clone repository
git clone https://github.com/KarunyaKalk/Riskline.git
cd Riskline

# 2. Copy environment file
cp backend/.env.example backend/.env

# 3. Boot local multi-container stack
docker compose up --build
```

Access local endpoints:
- **Mission Control Web App**: `http://localhost:5173` (or `http://localhost:80` via Docker)
- **FastAPI OpenAPI Specs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

---

## 🧪 Running Automated Tests

```bash
# Run backend Pytest suite (30 unit & integration tests)
PYTHONPATH=backend .venv/bin/pytest backend/tests -v

# Run frontend type-check, build & Vitest suite
cd frontend
npm run type-check
npm test
npm run build
```

---

## 📚 Documentation Index

- [ARCHITECTURE.md](ARCHITECTURE.md) — Comprehensive technical architecture, database schemas, and RAG vector pipeline breakdown.
- [docs/deployment.md](docs/deployment.md) — Self-hosting, multi-stage Docker builds, and automated database backup strategy.
- [docs/power-bi-setup.md](docs/power-bi-setup.md) — Connecting Power BI Desktop to the API export feed.
- [docs/onboarding-guide.md](docs/onboarding-guide.md) — 10-minute admin quickstart guide for startup teams.
- [CONTRIBUTING.md](CONTRIBUTING.md) — Developer setup, code standards, and PR guidelines.
- [CHANGELOG.md](CHANGELOG.md) — Chronological release notes for `v1.0.0`.
