from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai_sessions,
    auth,
    clinical_history,
    consultations,
    health,
    patients,
)

api_router = APIRouter()

# Authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Health endpoints
api_router.include_router(health.router, tags=["Health"])

# Patient profile endpoints
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])

# Consultation endpoints
api_router.include_router(
    consultations.router, prefix="/consultations", tags=["Consultations"]
)

# Clinical history endpoints (nested under consultations)
api_router.include_router(
    clinical_history.router,
    prefix="/consultations/{consultation_id}/history",
    tags=["Clinical History"],
)

# AI session + message endpoints
# Routes are self-prefixed in the endpoint file:
#   POST /consultations/{consultation_id}/ai-sessions
#   GET  /ai-sessions/{session_id}
#   POST /ai-sessions/{session_id}/messages
#   GET  /ai-sessions/{session_id}/messages
#   POST /ai-sessions/{session_id}/complete
api_router.include_router(ai_sessions.router, tags=["AI Sessions"])
