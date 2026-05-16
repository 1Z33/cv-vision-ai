"""
Routeur principal agrégateur de toutes les routes API v1.
"""

from fastapi import APIRouter

from app.api.v1 import auth, users, cvs, interviews, jobs, matching

api_router = APIRouter(prefix="/api/v1")

# Endpoints publics de disponibilité
@api_router.get("/health", tags=["Health"])
async def api_health_check():
    return {"status": "healthy", "version": "1.0.0", "api": "v1"}

@api_router.get("/ping", tags=["Health"])
async def api_ping():
    return {"message": "pong"}

# Inclusion des sous-routeurs
api_router.include_router(auth.router, prefix="/auth", tags=["Authentification"])
api_router.include_router(users.router, prefix="/users", tags=["Utilisateurs"])
api_router.include_router(cvs.router, prefix="/cvs", tags=["CVs"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["Entretiens"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Offres d'emploi"])
api_router.include_router(matching.router, prefix="/matches", tags=["Matching"])