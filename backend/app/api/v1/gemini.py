from fastapi import APIRouter

from app.services.analyzer_engine import CVAnalyzerEngine

router = APIRouter()


@router.get("/gemini-status")
async def gemini_status():
    """Vérifie si Gemini est disponible (pour le frontend).

    Endpoint public.
    """
    analyzer = CVAnalyzerEngine()
    enabled = bool(getattr(analyzer.gemini, "enabled", False))
    return {
        "enabled": enabled,
        "model": "gemini-2.0-flash" if enabled else None,
    }


@router.get("/gemini-limit")
async def gemini_limit_status():
    """Retourne le statut du rate limiter Gemini (plan gratuit)."""
    from app.services.gemini_cv_analyzer import gemini_limiter

    return gemini_limiter.get_status()


