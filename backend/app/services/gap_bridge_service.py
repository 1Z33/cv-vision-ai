"""Service Gap Bridge — Génération plan d'action compétences."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis
from app.models.gap_bridge import GapBridgePlan, GapBridgeItem


# Charger le corpus de ressources
RESOURCES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "gap_resources.json")


def load_resources() -> Dict:
    """Charge le mapping skills → ressources."""
    try:
        with open(RESOURCES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


RESOURCES_CORPUS = load_resources()


class GapBridgeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_plan(self, cv_id: str, user_id: str) -> GapBridgePlan:
        """Génère un plan d'action à partir de l'analyse d'un CV."""

        # 1. Récupérer l'analyse
        result = await self.db.execute(select(Analysis).where(Analysis.cv_id == cv_id))
        analysis = result.scalar_one_or_none()

        if not analysis:
            raise ValueError("Analyse non trouvée pour ce CV")

        # 2. Vérifier s'il y a des skills manquants
        missing_skills = analysis.missing_skills or []
        if not missing_skills:
            raise ValueError("Aucune compétence manquante identifiée — le CV est déjà complet !")

        # 3. Mapper skills → ressources
        plan_items: List[dict] = []
        total_duration = 0

        for skill in missing_skills:
            skill_lower = (skill or "").lower()
            resource_found = False

            for category, skills in RESOURCES_CORPUS.items():
                for corpus_skill, resources in skills.items():
                    if not isinstance(resources, list) or not resources:
                        continue

                    corpus_skill_lower = str(corpus_skill).lower()
                    if corpus_skill_lower in skill_lower or skill_lower in corpus_skill_lower:
                        resource = resources[0]
                        plan_items.append(
                            {
                                "skill_name": skill,
                                "category": category,
                                "resource_title": resource["title"],
                                "resource_url": resource["url"],
                                "resource_type": resource.get("type", "documentation"),
                                "duration_hours": resource.get("duration_hours", 10),
                                "is_free": resource.get("free", True),
                            }
                        )
                        total_duration += resource.get("duration_hours", 10)
                        resource_found = True
                        break
                if resource_found:
                    break

            if not resource_found:
                # fallback générique
                plan_items.append(
                    {
                        "skill_name": skill,
                        "category": "general",
                        "resource_title": f"Apprendre {skill}",
                        "resource_url": f"https://www.google.com/search?q=apprendre+{str(skill).replace(' ', '+')}",
                        "resource_type": "search",
                        "duration_hours": 20,
                        "is_free": True,
                    }
                )
                total_duration += 20

        # 4. Créer le plan
        plan = GapBridgePlan(
            user_id=user_id,
            cv_id=cv_id,
            analysis_id=str(analysis.id),
            missing_skills=missing_skills,
            total_resources=len(plan_items),
            total_duration_hours=total_duration,
        )
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)

        # 5. Créer les items
        for item_data in plan_items:
            item = GapBridgeItem(plan_id=plan.id, **item_data)
            self.db.add(item)

        await self.db.commit()
        await self.db.refresh(plan)

        return plan

    async def get_plan(self, plan_id: str, user_id: str) -> GapBridgePlan:
        """Récupère un plan avec vérification ownership."""
        result = await self.db.execute(select(GapBridgePlan).where(GapBridgePlan.id == plan_id))
        plan = result.scalar_one_or_none()

        if not plan:
            raise ValueError("Plan non trouvé")

        if str(plan.user_id) != str(user_id):
            raise ValueError("Accès non autorisé")

        return plan

    async def update_progress(
        self,
        item_id: str,
        user_id: str,
        status: str,
        progress_percent: Optional[int] = None,
    ) -> GapBridgeItem:
        """Met à jour la progression d'un item."""

        result = await self.db.execute(select(GapBridgeItem).where(GapBridgeItem.id == item_id))
        item = result.scalar_one_or_none()

        if not item:
            raise ValueError("Item non trouvé")

        if str(item.plan.user_id) != str(user_id):
            raise ValueError("Accès non autorisé")

        item.status = status

        if progress_percent is not None:
            item.progress_percent = min(100, max(0, int(progress_percent)))

        if status == "in_progress" and not item.started_at:
            item.started_at = datetime.utcnow()

        if status == "completed":
            item.progress_percent = 100
            item.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(item)

        return item

    async def get_summary(self, plan_id: str, user_id: str) -> Dict:
        """Retourne un résumé de progression."""
        plan = await self.get_plan(plan_id, user_id)

        items = plan.items
        total = len(items)
        completed = sum(1 for i in items if i.status == "completed")
        in_progress = sum(1 for i in items if i.status == "in_progress")

        overall_progress = sum(i.progress_percent for i in items) // max(total, 1)

        return {
            "plan_id": plan_id,
            "total_items": total,
            "completed_items": completed,
            "in_progress_items": in_progress,
            "overall_progress_percent": overall_progress,
            "total_duration_hours": plan.total_duration_hours,
            "estimated_completion": self._estimate_completion(items)
            if completed < total
            else "Terminé",
        }

    def _estimate_completion(self, items: List[GapBridgeItem]) -> Optional[str]:
        """Estime la date de fin basée sur la progression."""

        remaining_hours = sum(
            i.duration_hours * (100 - i.progress_percent) / 100
            for i in items
            if i.status != "completed"
        )

        # Hypothèse : 5h/semaine
        weeks = remaining_hours / 5
        if weeks < 1:
            return "Moins d'une semaine"
        if weeks < 4:
            return f"Environ {int(weeks)} semaines"
        return f"Environ {int(weeks / 4)} mois"

