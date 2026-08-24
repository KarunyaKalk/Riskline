# Self-Hosting & Production Deployment Guide

This guide walks through deploying **Riskline** to production using multi-stage Docker containers, managed PostgreSQL (pgvector), Redis, and automated database backup routines.

---

## 1. Target Hosting Platform Recommendation

For small to mid-sized engineering teams, we recommend **Render** or **Railway**:
- **Render**: Supports managed PostgreSQL with `pgvector` extension out-of-the-box, managed Redis instance, automatic TLS certificates, and native multi-service deployment from GitHub.
- **Railway**: Alternative lightweight developer platform with one-click Postgres+Redis provisioning.

---

## 2. Environment Variables Configuration

Set the following environment variables in your hosting provider's secret manager:

```ini
# Core Configuration
ENVIRONMENT=production
DEBUG=false
PROJECT_NAME="Riskline Mission Control"

# Database & Redis
DATABASE_URL=postgresql://user:password@pg-host:5432/riskline_db
REDIS_URL=redis://redis-host:6379/0

# Security Secrets (Generate using openssl rand -hex 32)
JWT_SECRET_KEY=e83a4f...
JWT_REFRESH_SECRET_KEY=7c12b9...

# Allowed CORS Origins (No wildcard *)
CORS_ORIGINS="https://riskline.yourcompany.com,http://localhost:5173"

# AI Provider Credentials (Optional; defaults to Mock engine if blank)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=

# Error Tracking (Optional)
SENTRY_DSN=https://...
```

---

## 3. Production Deployment via Docker Compose

```bash
# 1. Clone repository on production host
git clone https://github.com/KarunyaKalk/Riskline.git
cd Riskline

# 2. Configure production .env
cp backend/.env.example .env

# 3. Build & launch production stack in detached mode
docker compose -f docker-compose.prod.yml up --build -d

# 4. Execute database Alembic migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

## 4. Database Backup Strategy

Run automated daily backups using the provided backup script:

```bash
# Test backup script manually
./infra/scripts/backup_db.sh

# Configure daily crontab (e.g. at 02:00 AM)
0 2 * * * /bin/bash /path/to/Riskline/infra/scripts/backup_db.sh >> /var/log/riskline_backup.log 2>&1
```

The script compresses database dumps (`.sql.gz`) and automatically retains the last 14 days of backups.
