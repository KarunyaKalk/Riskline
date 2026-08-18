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

### 2. Key Architectural Decisions

#### Decision: TeamMember vs User Model
- **Choice**: Implemented `TeamMember` as a separate, lightweight roster table scoped by `org_id` with an optional `user_id` foreign key (`nullable=True`).
- **Rationale**: In real-world engineering teams, admins and leads need to map out team rosters and assign deployment changes or risk reviews to individuals before those team members have registered a platform account. Having `TeamMember` as a roster entity allows unboarded team members to exist on changes/notes; when a user completes registration, their `user_id` is linked to their `TeamMember` profile.

#### Decision: Audit Log Strategy From Day One
- **Choice**: Built `AuditLog` table and `record_audit_log` helper into the backend core on Day 1.
- **Rationale**: Multi-tenant platforms operating in enterprise/DevOps environments require strict auditability. Recording security mutations (`USER_SIGNUP`, `USER_LOGIN`) from the outset prevents security gaps and avoids complex retrofitting.

#### Decision: Multi-Tenant Data Isolation Pattern
- **Choice**: Enforced `OrgScopedMixin` on every domain model (except `Organization`).
- **Rationale**: Every table containing org-specific data guarantees an `org_id` column with an index and foreign key cascade. API route dependencies extract `org_id` directly from verified JWT claims.

---

### 3. What's Next (Day 2 Roadmap)
- **Change Data Ingestion Pipeline**: Endpoints and parsers for deployment logs, PR summaries, and document/PDF uploads.
- **Mock LLM & Risk Assessment Engine**: Pipeline for generating technical risk scores and plain-language stakeholder summaries.

---

### 4. Open Questions
- None. Day 1 foundation is fully functional and ready for Day 2 ingestion features.
