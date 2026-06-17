"""
Routeur principal agrégateur de toutes les routes API v1.
"""

from fastapi import APIRouter

from app.api.v1 import auth, users, cvs, interviews, jobs, matching, gemini, salary
from app.api.v1 import cache as cache_routes
from app.api.v1 import gap_bridge as gap_bridge_routes
from app.api.v1 import interview_live_ws as interview_live_ws_routes

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(interview_live_ws_routes.router, prefix="", tags=["VocalInterviewLive"])

# Routes publiques
api_router.include_router(gemini.router, tags=["Gemini"])


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

from app.routes import interview as vocal_interview_routes
api_router.include_router(vocal_interview_routes.router, tags=["VocalInterview"])

api_router.include_router(jobs.router, prefix="/jobs", tags=["Offres d'emploi"])


api_router.include_router(matching.router, prefix="/matches", tags=["Matching"])
api_router.include_router(salary.router, prefix="/salary", tags=["Salary Predictor"])
api_router.include_router(gap_bridge_routes.router)


# Admin cache routes
api_router.include_router(cache_routes.router)


