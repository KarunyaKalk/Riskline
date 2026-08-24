import os
from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.api.v1 import api_v1_router
from app.core.config import settings
from app.core.logging import RequestContextMiddleware, setup_structured_logging
from app.models.change import Change
from app.models.organization import Organization
from app.models.risk_analysis import RiskAnalysis
from app.models.user import User, UserRole

# Initialize structured JSON logging
setup_structured_logging()

# Sentry Error Tracking Initialization (Stubs if SENTRY_DSN provided)
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.2,
            environment=settings.ENVIRONMENT,
        )
    except ImportError:
        pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="DevOps Change Intelligence & Risk Analysis Platform API v1.0",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration supporting credentials (cookies)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestContextMiddleware)

app.include_router(api_v1_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }


# System Usage Metrics Endpoint (Admin restricted)
metrics_router = APIRouter(prefix="/api/v1/audit", tags=["Metrics"])


@metrics_router.get(
    "/metrics",
    summary="Platform System Usage Metrics",
    description="Returns aggregate usage metrics across all organizations. Restricted to Admin role.",
)
def get_system_metrics(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    total_orgs = db.query(func.count(Organization.id)).scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_changes = db.query(func.count(Change.id)).scalar() or 0
    analyzed_changes = db.query(func.count(RiskAnalysis.id)).scalar() or 0

    return {
        "timestamp": func.now(),
        "total_organizations": total_orgs,
        "total_registered_users": total_users,
        "total_changes_submitted": total_changes,
        "total_risk_analyses_run": analyzed_changes,
        "system_status": "operational",
    }


app.include_router(metrics_router)
