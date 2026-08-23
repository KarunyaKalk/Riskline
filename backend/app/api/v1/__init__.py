from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.roster import router as roster_router
from app.api.v1.notes import router as notes_router
from app.api.v1.progress import router as progress_router
from app.api.v1.changes import router as changes_router
from app.api.v1.orgs import router as orgs_router
from app.api.v1.audit import router as audit_router
from app.api.v1.chat import router as chat_router
from app.api.v1.events import router as events_router
from app.api.v1.notifications import router as notifications_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(roster_router)
api_v1_router.include_router(notes_router)
api_v1_router.include_router(progress_router)
api_v1_router.include_router(changes_router)
api_v1_router.include_router(orgs_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(events_router)
api_v1_router.include_router(notifications_router)
