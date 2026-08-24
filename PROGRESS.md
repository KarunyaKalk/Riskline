# DevOps Risk Platform — Progress & Architecture Log

## Day 1 — Foundation (Completed)

### 1. What's Built
- **Monorepo Layout**: Initialized `backend/`, `frontend/`, `infra/`, `docs/` with root `.editorconfig`, `LICENSE` (MIT), and `README.md`.
- **Docker Stack Scaffolding**: Configured `docker-compose.yml` defining `postgres` (pgvector:pg16), `redis` (7-alpine), `backend` (FastAPI), and `frontend` (React + Nginx static server), complete with healthchecks for each service.
- **Core Multi-Tenant Database Schema**:
  - `Organization`: `id`, `name`, `slug` (unique), `plan`, `created_at`.
  - `User`: `id`, `org_id`, `email`, `hashed_password` (Argon2id), `role` (`admin`, `engineer`, `business_ops`, `viewer`), `status`, `created_at`.
  - `TeamMember`: `id`, `org_id`, `user_id` (nullable FK), `name`, `email`, `role`, `status`, `created_at`.
  - `Change`: `id`, `org_id`, `title`, `description`, `status`, `author_id`, `deployment_date`, `risk_score`, `metadata_json`, timestamps.
  - `RiskAnalysis`: `id`, `org_id`, `change_id`, `technical_summary`, `business_summary`, `risk_level`, `recommendations_json`, `created_at`.
  - `Note`: `id`, `org_id`, `title`, `content`, `author_id`, `tags_json`, timestamps.
  - `ProjectProgress`: `id`, `org_id`, `title`, `status`, `progress_pct`, `owner_id`, `target_date`, timestamps.
  - `ChatMessage`: `id`, `org_id`, `user_id`, `session_id`, `role`, `content`, `created_at`.
  - `AuditLog`: `id`, `org_id`, `actor_user_id`, `action`, `target_type`, `target_id`, `metadata_json`, `created_at`.
- **Alembic Migrations**: First migration (`001_initial_schema.py`) establishes the full database schema and vector extension.
- **Authentication & RBAC**:
  - `/signup`: Creates Organization, Admin User, initial TeamMember entry, and logs `USER_SIGNUP` audit event.
  - `/login`: Verifies Argon2id password hash, logs `USER_LOGIN` audit event, issues JWT access/refresh tokens, and sets `HttpOnly` cookies.
  - Dependencies: `get_current_user`, `get_current_org`, and `require_roles(...)` primitive for RBAC (`admin`, `engineer`, `business_ops`, `viewer`).
- **React + Vite + TypeScript Frontend**:
  - Configured TypeScript (`tsconfig.json`, `@types`, `type-check` script).
  - Built `AuthContext` provider, `ProtectedRoute` shell, `Login`, `Signup`, and `Dashboard` pages.
  - Added Docker multi-stage build + Nginx static server configuration (`frontend/Dockerfile`, `frontend/nginx.conf`).
- **CI & Test Suite**:
  - GitHub Actions workflow (`.github/workflows/ci.yml`) running Postgres, Alembic migrations, Pytest backend tests, and frontend `type-check` + `build`.
  - Automated tests covering signup, login, unauthenticated 401 rejection, RBAC 403 authorization checks, and cross-tenant data isolation.

---

## Day 2 — Core Domain Backend (Completed)

### 1. What's Built
- **Team Roster Endpoints (`/api/v1/team-members`)**: Full org-scoped CRUD for managing team members. Restricted to Admin role for create, update, and delete operations. Readable by all org members.
- **Notes & Brainstorm Board (`/api/v1/notes`)**: Full org-scoped CRUD with support for tags (`idea`, `blocker`, `decision`, `question`), tag filtering (`?tag=blocker`), author filtering (`?author_id=...`), and pagination (`skip`, `limit`). Protected so only the note author or Organization Admin can modify or delete a note.
- **Project Progress Tracker (`/api/v1/project-progress`)**: Full org-scoped CRUD allowing Admin/Engineer roles to update project milestones and progress percentages, while all org users can view status.
- **Change Management (`/api/v1/changes`)**: Full org-scoped CRUD for deployment and architectural changes. Sets `author_id` strictly to the authenticated `current_user.id` for auditability. Includes status filtering (`?status=deployed`), author filtering, and pagination.
- **Org Management & Teammate Invites (`/api/v1/orgs`)**:
  - Introduced `OrgInvite` model (`org_id`, `email`, `role`, `token`, `status`, `expires_at`).
  - `POST /api/v1/orgs/invites`: Generates a 48-hour secure invite token (Admin only).
  - `GET /api/v1/orgs/invites/{token}`: Inspects invite details.
  - `POST /api/v1/orgs/invites/accept`: Accepts invite and registers user under the inviting organization.
  - `PUT /api/v1/orgs/members/{user_id}/role`: Modifies member roles with sole-admin demotion protection.
  - `DELETE /api/v1/orgs/members/{user_id}`: Removes members from org with self-removal protection.
- **Audit Log Integration**: Integrated `record_audit_log` into every single mutation endpoint across the system (`TEAM_MEMBER_CREATED`, `NOTE_DELETED`, `PROJECT_PROGRESS_UPDATED`, `CHANGE_CREATED`, `USER_INVITED`, `INVITE_ACCEPTED`, `MEMBER_ROLE_UPDATED`, `MEMBER_REMOVED`). Exposed `GET /api/v1/audit-logs` endpoint with pagination and action filtering.
- **Redis-Backed Rate Limiting**: Added `RateLimiter` dependency enforcing per-user limits (60 mutating requests/min) using Redis with an in-memory sliding window fallback for test environments.
- **OpenAPI Documentation**: Enriched FastAPI auto-generated OpenAPI documentation with response models, status codes, query descriptions, and schema examples.

---

## Day 3 — AI Core & Risk Analysis Pipeline (Completed)

### 1. What's Built
- **LLM Client Abstraction (`llm_client.py`)**:
  - Provider-agnostic interface supporting OpenAI (`gpt-4o-mini`), Gemini (`gemini-1.5-flash`), and a zero-cost Mock heuristic fallback engine.
  - Structured output validation using Pydantic `RiskAnalysisOutput` (`risk_level`, `risk_score`, `technical_summary`, `business_summary`, `recommendations`, `is_degraded`).
  - Automatic retry with exponential backoff (2 attempts) and timeout enforcement (15s).
  - Graceful degradation: Never fails user requests on API errors; falls back to mock heuristic engine with `is_degraded = True`.
- **Embeddings & `pgvector` RAG Pipeline (`embedding_service.py`)**:
  - Added `ChangeEmbedding` model and Alembic migration `003_pgvector_change_embeddings.py`.
  - Document chunking strategy (800-character sliding window with 150-character overlap).
  - Embedding generation: OpenAI `text-embedding-3-small` (1536 dims) when OpenAI API key is present; deterministic 1536-dimensional Hash-Vectorizer fallback for mock/offline/CI environments.
  - Semantic vector search (`search_similar_chunks`) strictly scoped to the requesting organization (`WHERE org_id == current_user.org_id`), guaranteeing zero cross-tenant vector data leakage.
- **PDF Ingestion Parser (`pdf_service.py`)**:
  - File size validation (10MB limit) and PDF magic header check (`%PDF`).
  - Text extraction using `pypdf.PdfReader`.
  - Clear error handling for non-PDFs or documents containing no extractable text.
  - `POST /api/v1/changes/upload-pdf` endpoint for uploading PDF change specifications.
- **Risk Analysis Engine (`risk_engine.py`)**:
  - `run_risk_analysis_pipeline`: Combines change title/description with historical RAG context, invokes LLM client, stores `RiskAnalysis` record, indexes change text into `ChangeEmbedding`, updates `Change` status and risk score, and records audit logs (`RISK_ANALYSIS_COMPLETED`).
  - Background async execution via FastAPI `BackgroundTasks`.
  - Endpoints: `POST /api/v1/changes/{id}/analyze` and `GET /api/v1/changes/{id}/risk-analysis`.

---

## Day 4 — Chat, Real-Time Updates & Notifications (Completed)

### 1. What's Built
- **Streaming Chatbot with Audience Modes (`chat_service.py`, `/api/v1/chat`)**:
  - Token-by-token streaming responses via Server-Sent Events (SSE) at `POST /api/v1/chat/stream`.
  - Shared organization chat threads by `session_id` with `user_id` message attribution.
  - Refined system prompts for `technical`, `business`, and `auto-detect` audience translation modes with few-shot examples.
  - Contextual grounding using RAG retrieval from `embedding_service`.
  - `GET /api/v1/chat/history` endpoint to retrieve persistent thread messages.
- **Real-Time Org Event Broadcasting (`events.py`, `/api/v1/events`)**:
  - `EventBroadcaster` publisher/subscriber manager in `backend/app/core/events.py`.
  - SSE endpoint `GET /api/v1/events/stream` broadcasting live changes, notes, and alerts strictly for the requesting tenant (`WHERE org_id == current_user.org_id`).
  - Integrated live event publishing into `create_change` and `run_risk_analysis_pipeline`.
- **Notifications & User Delivery Preferences (`notification_service.py`, `/api/v1/notifications`)**:
  - Models `Notification` and `NotificationPreference` with Alembic migration `004_notifications_schema.py`.
  - Automatic notification triggering when a deployment change evaluates at `high` or `critical` risk (`risk_score >= 7.0`).
  - Support for in-app notification alerts, email delivery stubs, and Slack webhook alert stubs.
  - Endpoints for listing notifications, marking read, and updating user preferences (`inapp_enabled`, `email_enabled`, `slack_enabled`, `min_risk_level`).

---

## Day 5 — Frontend Application & Design System (Completed)

### 1. What's Built
- **Mission Control Design System (`index.css`)**:
  - Dark Slate Mission Control theme (`#0B0F19` background, `#111827` cards, `#1F2937` borders).
  - Neon Cyan (`#06B6D4`) data stream accents, Electric Violet (`#8B5CF6`) AI badges.
  - Risk Score Gauge tokens: Emerald (`#10B981`) Low, Amber (`#F59E0B`) Med, Rose (`#EF4444`) High/Critical.
  - Accessible WCAG AA contrast ratio (>4.5:1), visible focus rings (`focus-visible:ring-2 focus-visible:ring-cyan-500`), and `@media (prefers-reduced-motion)` overrides.
- **Frontend Component & View Suite**:
  - `Header.tsx` & `Navigation.tsx`: Sidebar navigation, org badge, role pill, live SSE connection status dot, notification bell popover with unread counter, and AI Assistant drawer toggle.
  - `DashboardPage.tsx`: Aggregate risk cards (Total Changes, Avg Risk Score, High Risk Alerts count, Deployed count), project progress bars, recent changes table, and live SSE event feed.
  - `ChangesPage.tsx` & `RiskAnalysisDetailPage.tsx`: Deployment change submit modal (text or PDF upload), background job status polling, side-by-side Technical Summary (for SREs) + Business Summary (for Executives) breakdown cards, and action recommendations checklist.
  - `ChatDrawer.tsx`: Slide-over AI Assistant drawer with real-time SSE token streaming, Audience Mode toggle pills (`Technical`, `Business`, `Auto-Detect`), and persistent history.
  - `NotesPage.tsx`: Brainstorm board grid with tag filters (`all`, `idea`, `blocker`, `decision`, `question`), optimistic note creation, and author/admin deletion permissions.
  - `TeamRosterPage.tsx`, `OrgSettingsPage.tsx`, `AuditLogsPage.tsx`: Role management, 48-hour invite token generator, sole-admin protection rules, and filterable audit event logs.
- **Testing Suite**:
  - Vitest component tests in `src/__tests__/` (Header and Navigation components passing).
  - Playwright E2E integration test spec in `e2e/full_flow.spec.ts`.

---

## Day 6 — Integrations, Security Hardening & Performance (Completed)

### 1. What's Built & Verified

#### Power BI Export Integration
- **API Key Management (`export.py`, `api_key.py`)**: Admin-restricted endpoint `POST /api/v1/export/api-keys` issuing 32-character secret keys (`rk_live_...`), stored as SHA-256 hashes in database table `api_keys` with Alembic migration `005_powerbi_and_password_resets.py`.
- **Power BI JSON Export Endpoint (`GET /api/v1/export/power-bi`)**: Read-only endpoint authenticated via `X-API-Key` header or `?api_key=...` query parameter. Returns tabular change history, risk scores, summaries, and milestone progress filtered strictly by the key owner's `org_id`.
- **Documentation (`docs/power-bi-setup.md`)**: Step-by-step connection guide for Power BI Desktop Web Data Source with custom header authentication and scheduled refresh.

#### Security Pass & Audit Checklist
| Security Item | Status | Verification & Implementation Notes |
| :--- | :---: | :--- |
| **Tenant Isolation Audit** | PASSED | Re-audited all query paths (`Change`, `Note`, `TeamMember`, `ProjectProgress`, `ChatMessage`, `AuditLog`, `Notification`, `ApiKey`). Confirmed `WHERE org_id == current_user.org_id` on all endpoints. |
| **XSS & Input Sanitization** | PASSED | Pydantic strict string validation on inputs; React JSX auto-escaping prevents script injection on all UI rendered text. |
| **File Upload Hardening** | PASSED | Server-side 10MB limit enforcement, `%PDF` magic header byte inspection, and graceful exception handling for malformed/corrupted PDFs (`test_malformed_pdf_upload_rejection`). |
| **CORS Configuration** | PASSED | Explicit `CORSMiddleware` configured via `settings.cors_origin_list` (`http://localhost:5173`, `http://127.0.0.1:5173`). Wildcard `*` disabled. |
| **Secrets Hygiene** | PASSED | Secrets loaded exclusively via pydantic-settings `.env`; password hashes use Argon2id; API keys stored as SHA-256 hashes; secrets never logged or returned in responses. |
| **Password Reset Flow** | PASSED | `POST /auth/forgot-password` and `POST /auth/reset-password` with 1-hour expiration and single-use invalidation (`PasswordResetToken`). |
| **Auth Rate Limiting** | PASSED | `AuthRateLimiter` enforces 5 attempts/min on `/login`, `/signup`, and password reset endpoints. |
| **Vulnerability Audit** | PASSED | `npm audit fix` executed. Resolved dependency vulnerabilities. |

#### Performance & Load Benchmarks
- **Load Test Script (`backend/scripts/benchmark_load.py`)**:
  - `/health`: **800.4 req/s** (50 requests in 0.062s)
  - `GET /api/v1/changes`: **291.2 req/s** (50 requests in 0.172s)
  - `POST /api/v1/changes`: **81.0 req/s** (10 mutation requests in 0.124s including async AI pipeline execution and high-risk notification dispatch)
- **Database Indexes**: Indexed foreign keys and search columns (`org_id`, `user_id`, `created_at`, `status`, `key_hash`, `token_hash`).

---

### 2. Test Coverage Summary
- **Backend Pytest Suite**: **30 passing tests** (`PYTHONPATH=backend .venv/bin/pytest backend/tests -v`).
- **Frontend Vitest Suite**: **2 passing component test suites** (`npm test` in `frontend/`).
- **Frontend Type-Check & Build**: `npm run type-check && npm run build` passing with 0 errors.

---

### 3. Open Questions / Findings for User
- **Auth Rate Limiter In-Memory Fallback**: When Redis is not connected during local dev or unit tests, the rate limiter falls back to an in-memory sliding window store. We added an autouse fixture in `conftest.py` to reset the store between unit tests so rate limits don't overflow across test cases.
