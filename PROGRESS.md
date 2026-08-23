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

### 2. Key Architectural Decisions

#### Decision: Server-Sent Events (SSE) Protocol for Chat & Live Events
- **Choice**: Selected SSE (`text/event-stream`) over WebSockets for both token streaming and real-time dashboard broadcasts.
- **Rationale**: SSE is HTTP-native, simpler, proxy-friendly behind Nginx, handles token streaming out of the box, and features automatic client reconnection.

#### Decision: Shared Org Chat Threads
- **Choice**: Chat sessions are shared organization-wide with `user_id` message attribution.
- **Rationale**: Directly reinforces the core product value proposition: cross-team alignment and transparency between technical engineers and business/ops leaders.

---

### 3. Test Coverage Summary

Extensive test coverage (27 total Pytest cases passing):
- **Chat & Real-Time Tests (`test_chat_and_realtime.py`)**: SSE token streaming, audience mode translation, tenant/session chat isolation, tenant-isolated SSE event broadcasting, high-risk notification triggering & preference controls.
- **AI Pipeline Tests (`test_ai_pipeline.py`)**: End-to-end PDF ingestion, invalid PDF rejection, strict cross-tenant RAG vector isolation, realistic deployment scenario assessments.
- **Roster Tests (`test_roster.py`)**: Full CRUD, Admin-only enforcement, Viewer 403 checks, cross-tenant isolation.
- **Notes Tests (`test_notes.py`)**: Full CRUD, tag filtering, author filtering, pagination, author/admin deletion checks, cross-tenant isolation.
- **Progress Tests (`test_progress.py`)**: Full CRUD, Admin/Engineer edit permissions, Viewer read-only checks, cross-tenant isolation.
- **Changes Tests (`test_changes.py`)**: Full CRUD, `author_id` linking to `current_user.id`, status filtering, pagination, cross-tenant isolation.
- **Org & Invite Tests (`test_orgs.py`)**: Invite token generation & acceptance, member role updates, sole-admin protection, member removal, cross-tenant isolation.
- **Rate Limiter Tests (`test_rate_limiter.py`)**: Rate limiting count enforcement & 429 response.
- **Auth Tests (`test_auth.py`)**: Signup, login, 401 unauthenticated rejection, 403 RBAC checks, cross-tenant isolation.

---

### 4. What's Next (Day 5 Roadmap)
- **Frontend Dashboard & Collaborative UI Surface**:
  - Connect React frontend to backend API endpoints (Changes, Notes, Roster, Progress, Risk Analyses).
  - Live SSE real-time feed integration & notification bell badge.
  - Interactive streaming chat drawer with audience mode toggle (`Technical` vs `Business`).

---

### 5. Open Questions for User
- Both Slack webhook and email notification stubs are built and integrated. Would you like to configure a specific Slack Webhook URL or SMTP server setting for Day 5?
