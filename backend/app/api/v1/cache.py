"""
Endpoints de monitoring et gestion du cache (admin).
"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.core.cache import (
    cv_analysis_cache,
    matching_cache,
    interview_questions_cache,
    invalidate_cv_cache,
)
from app.models.user import User

router = APIRouter(prefix="/cache", tags=["cache"])


async def require_admin(current_user: User = Depends(get_current_user)):
    """Vérifie que l'utilisateur est admin."""

    is_admin = (
        getattr(current_user, "role", None) == "admin"
        or getattr(current_user, "is_admin", False)
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Accès admin requis")
    return current_user


@router.get("/stats")
async def get_cache_stats(admin: User = Depends(require_admin)):
    """Statistiques de tous les caches."""

    cv_stats = cv_analysis_cache.get_stats()
    match_stats = matching_cache.get_stats()
    interview_stats = interview_questions_cache.get_stats()

    total_hits = cv_stats["hits"] + match_stats["hits"] + interview_stats["hits"]
    total_misses = (
        cv_stats["misses"] + match_stats["misses"] + interview_stats["misses"]
    )
    total_requests = total_hits + total_misses

    return {
        "cv_analysis": cv_stats,
        "matching": match_stats,
        "interview_questions": interview_stats,
        "summary": {
            "total_entries": cv_stats["size"]
            + match_stats["size"]
            + interview_stats["size"],
            "total_hits": total_hits,
            "total_misses": total_misses,
            "global_hit_rate_percent": round(
                (total_hits / total_requests * 100), 2
            )
            if total_requests > 0
            else 0,
        },
    }


@router.post("/clear/{cache_name}")
async def clear_cache(cache_name: str, admin: User = Depends(require_admin)):
    """Vide un cache spécifique.

    - `cv_analysis` : analyses CV
    - `matching` : résultats de matching
    - `interview_questions` : questions d'interview
    - `all` : tout vider
    """

    caches = {
        "cv_analysis": cv_analysis_cache,
        "matching": matching_cache,
        "interview_questions": interview_questions_cache,
    }

    if cache_name == "all":
        for cache in caches.values():
            cache.clear()
        return {
            "message": "Tous les caches ont été vidés",
            "cleared": list(caches.keys()),
        }

    if cache_name not in caches:
        raise HTTPException(
            status_code=400,
            detail=f"Cache inconnu. Choix: {', '.join(caches.keys())}, all",
        )

    caches[cache_name].clear()
    return {
        "message": f"Cache '{cache_name}' vidé",
        "cleared": [cache_name],
    }


@router.post("/invalidate/cv/{cv_id}")
async def invalidate_cv(cv_id: str, admin: User = Depends(require_admin)):
    """Invalide manuellement le cache d'un CV spécifique."""

    invalidated = invalidate_cv_cache(cv_id)
    return {
        "message": f"Cache invalidé pour CV {cv_id}",
        "entries_removed": invalidated,
    }

