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
- **AI Pipeline Test Suite (`test_ai_pipeline.py`)**:
  - Full mock-mode end-to-end test (PDF upload -> text extraction -> sliding-window chunking -> embedding -> RAG search -> risk engine -> persistence).
  - Cross-tenant RAG isolation test verifying Org B vector search returns 0 results from Org A confidential embeddings.
  - Sanity check verifying realistic risk scores across 5 deployment scenarios (Schema migration, Auth token rotation, K8s upgrade, Redis restart, CSS typo fix).

---

### 2. Key Architectural Decisions

#### Decision: Embedding Model Selection & Fallback Strategy
- **Choice**: Used OpenAI `text-embedding-3-small` (1536 dimensions) when API keys are configured, and a local deterministic 1536-dimensional Hash-Vectorizer for mock/offline/CI environments.
- **Rationale**: Avoids per-call embedding API costs and network latency during local development and automated CI testing while preserving identical 1536-dimensional vector geometry and cosine similarity logic across all environments.

#### Decision: Async Background Analysis Task Architecture
- **Choice**: PDF uploads and change risk analyses are processed asynchronously using FastAPI `BackgroundTasks`. The upload endpoint immediately returns `status = "processing"`.
- **Rationale**: LLM generation and embedding indexing can take several seconds. Returning immediately prevents HTTP request timeouts and provides a smooth client experience where the frontend polls `GET /api/v1/changes/{id}` for completion.

---

### 3. Test Coverage Summary

Extensive test coverage (23 total Pytest cases passing):
- **AI Pipeline Tests (`test_ai_pipeline.py`)**: End-to-end PDF ingestion, invalid PDF rejection, strict cross-tenant RAG vector isolation, realistic deployment scenario assessments.
- **Roster Tests (`test_roster.py`)**: Full CRUD, Admin-only enforcement, Viewer 403 checks, cross-tenant isolation.
- **Notes Tests (`test_notes.py`)**: Full CRUD, tag filtering, author filtering, pagination, author/admin deletion checks, cross-tenant isolation.
- **Progress Tests (`test_progress.py`)**: Full CRUD, Admin/Engineer edit permissions, Viewer read-only checks, cross-tenant isolation.
- **Changes Tests (`test_changes.py`)**: Full CRUD, `author_id` linking to `current_user.id`, status filtering, pagination, cross-tenant isolation.
- **Org & Invite Tests (`test_orgs.py`)**: Invite token generation & acceptance, member role updates, sole-admin protection, member removal, cross-tenant isolation.
- **Rate Limiter Tests (`test_rate_limiter.py`)**: Rate limiting count enforcement & 429 response.
- **Auth Tests (`test_auth.py`)**: Signup, login, 401 unauthenticated rejection, 403 RBAC checks, cross-tenant isolation.

---

### 4. What's Next (Day 4 Roadmap)
- **Interactive Stakeholder Chatbot & RAG Assistant**:
  - Chatbot session management (`ChatMessage` table).
  - Contextual Q&A retrieving relevant changes, notes, and risk analyses.
  - Tailored technical responses for engineers vs. plain-language explanations for business stakeholders.

---

### 5. Open Questions for User
- Did the risk assessment scores and summaries for the deployment scenarios (e.g. 8.2 for DB schema drop column, 1.8 for CSS typo fix) align with your expectations?
