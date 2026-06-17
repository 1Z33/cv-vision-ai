"""Endpoints Gap Bridge — Plan d'action compétences."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.services.gap_bridge_service import GapBridgeService
from app.schemas.gap_bridge import (
    GapBridgePlanResponse,
    GapBridgeCreateRequest,
    GapBridgeUpdateProgressRequest,
    GapBridgeSummaryResponse,
)

router = APIRouter(prefix="/gap-bridge", tags=["gap-bridge"])


@router.post("/generate", response_model=GapBridgePlanResponse)
async def generate_plan(
    request: GapBridgeCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Génère un plan d'action à partir de l'analyse d'un CV."""

    service = GapBridgeService(db)
    try:
        plan = await service.generate_plan(request.cv_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Charger les items
    await db.refresh(plan, ["items"])
    return plan


@router.get("/{plan_id}", response_model=GapBridgePlanResponse)
async def get_plan(
    plan_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Récupère un plan d'action."""

    service = GapBridgeService(db)
    try:
        plan = await service.get_plan(plan_id, current_user.id)
    except ValueError as e:
        error_msg = str(e).lower()
        if "non trouvé" in error_msg:
            raise HTTPException(status_code=404, detail=str(e))
        if "non autorisé" in error_msg:
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    await db.refresh(plan, ["items"])
    return plan


@router.post("/progress", response_model=GapBridgePlanResponse)
async def update_progress(
    request: GapBridgeUpdateProgressRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Met à jour la progression d'un item du plan."""

    service = GapBridgeService(db)
    try:
        item = await service.update_progress(
            request.item_id,
            current_user.id,
            request.status,
            request.progress_percent,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Retourner le plan mis à jour
    await db.refresh(item, ["plan"])
    plan = item.plan
    await db.refresh(plan, ["items"])
    return plan


@router.get("/{plan_id}/summary", response_model=GapBridgeSummaryResponse)
async def get_summary(
    plan_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Résumé de progression d'un plan."""

    service = GapBridgeService(db)
    try:
        summary = await service.get_summary(plan_id, current_user.id)
    except ValueError as e:
        error_msg = str(e).lower()
        if "non trouvé" in error_msg:
            raise HTTPException(status_code=404, detail=str(e))
        if "non autorisé" in error_msg:
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    return summary

