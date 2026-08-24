# Contributing to Riskline

Welcome to the **Riskline** codebase! We appreciate your contributions to improving DevOps deployment safety and AI risk assessment.

---

## 1. Local Development Workflow

```bash
# 1. Fork and clone repository
git clone https://github.com/KarunyaKalk/Riskline.git
cd Riskline

# 2. Setup Python Virtual Environment for Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# 3. Setup Frontend Dependencies
cd frontend
npm install
cd ..

# 4. Start Local Environment via Docker Compose
docker compose up
```

---

## 2. Testing & Quality Standards

Before submitting a Pull Request, ensure all tests and type checks pass cleanly:

```bash
# Backend Pytest Suite
PYTHONPATH=backend pytest backend/tests -v

# Frontend Type-Check, Build, and Component Tests
cd frontend
npm run type-check
npm test
npm run build
```

---

## 3. Architecture & Code Guidelines

- **Multi-Tenancy**: All database models representing tenant data MUST inherit `OrgScopedMixin` and include `org_id` foreign keys.
- **Tenant Isolation**: Every database query in API endpoints MUST explicitly filter by `WHERE org_id == current_user.org_id`.
- **Audit Logging**: Every mutation endpoint MUST invoke `record_audit_log(db, org_id, actor_user_id, action, target_type, target_id)`.
- **No Mock Fallback Failures**: Ensure background pipelines degrade gracefully without crashing user requests when third-party AI keys are unavailable.
