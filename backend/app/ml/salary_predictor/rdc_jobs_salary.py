"""
Salary Predictor Service for RDC
Estime les salaires basés sur le PIB/habitant, le secteur, la qualification,
la difficulté de l'entretien et l'expérience.

Sources: World Bank + RAID/CAJJ 2025 + ITIE RDC + OpenShores 2026
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path

# Configuration par défaut
GDP_PER_CAPITA_MONTHLY = 48  # USD (~580 USD/an)
EXCHANGE_RATE_CDF = 2800

DIFFICULTY_MULTIPLIERS = {
    "easy": 0.85,
    "medium": 1.0,
    "hard": 1.25,
    "expert": 1.5
}

QUALIFICATION_MULTIPLIERS = {
    1: 0.75,   # Ouvrier/non qualifié
    2: 0.90,   # Semi-qualifié
    3: 1.10,   # Qualifié
    4: 1.35,   # Cadre
    5: 1.60    # Expert
}

# Conseils de négociation par secteur
NEGOTIATION_TIPS = {
    "mines": [
        "Le secteur minier paie les meilleurs salaires en RDC — négociez vos primes de risque.",
        "Demandez une assurance santé internationale (maladie professionnelle fréquente).",
        "Le logement et le transport sont souvent pris en charge par l'employeur.",
        "Vérifiez si vous êtes employé direct ou sous-traitant (grande différence de salaire).",
        "Le salaire décent à Kolwezi est estimé à 520 USD/mois (RAID 2025) — utilisez cette référence."
    ],
    "ong": [
        "Les ONG internationales appliquent des grilles salariales transparentes.",
        "Négociez les indemnités de logement et de transport (souvent 30-50% du package).",
        "Demandez une couverture santé internationale.",
        "Les contrats sont généralement à durée déterminée — prévoyez une clause de renouvellement.",
        "L'expérience sur le terrain en RDC est très valorisée par les ONG."
    ],
    "telecom": [
        "Le secteur télécom est en forte croissance en RDC — les compétences techniques sont rares.",
        "Négociez des formations certifiantes (Cisco, AWS, etc.) prises en charge.",
        "Le télétravail est de plus en plus accepté pour les postes IT.",
        "Les développeurs spécialisés (IA, cloud, cybersécurité) sont très demandés."
    ],
    "banque": [
        "Le secteur bancaire en RDC est en expansion — les profils bilingues sont valorisés.",
        "Négociez les primes de performance (souvent liées aux objectifs).",
        "La microfinance offre des opportunités pour les profils juniors."
    ],
    "sante": [
        "Le secteur santé manque cruellement de personnel qualifié en RDC.",
        "Les cliniciens privés paient mieux que le secteur public.",
        "Une certification internationale augmente significativement votre valeur.",
        "Négociez les gardes et les astreintes (souvent mal rémunérées)."
    ],
    "education": [
        "Le secteur éducatif privé (écoles, universités) paie mieux que le public.",
        "Les professeurs d'université avec doctorat ont un statut privilégié.",
        "Les cours particuliers et le consulting sont des revenus complémentaires courants."
    ],
    "default": [
        "Le salaire moyen en RDC est d'environ 125 USD/mois — valorisez vos compétences spécifiques.",
        "Les avantages en nature (logement, transport) peuvent représenter 30-50% du package.",
        "Prévoyez une clause de révision salariale indexée sur l'inflation (15-20%/an en RDC).",
        "Mentionnez vos réalisations chiffrées (ex: 'j'ai augmenté la productivité de 20%').",
        "Ne donnez pas votre salaire actuel, donnez une fourchette basée sur le marché."
    ]
}


class SalaryPredictor:
    """Prédicteur de salaire pour la RDC."""

    def __init__(self, jobs_file: Optional[str] = None):
        if jobs_file is None:
            base_dir = Path(__file__).parent.parent
            jobs_file = base_dir / "data" / "jobs_rdc.json"

        with open(jobs_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.jobs = data["jobs"]
        self.sectors = data["sectors"]
        self.metadata = data.get("_metadata", {})
        self.gdp_monthly = self.metadata.get("gdp_per_capita_monthly_usd", GDP_PER_CAPITA_MONTHLY)

    def list_jobs(self) -> List[Dict]:
        """Liste tous les métiers disponibles."""
        return [
            {
                "slug": slug,
                "display_name": info["display_name"],
                "sector": info["sector"],
                "display_sector": info["display_sector"],
                "qualification": info["qualification"]
            }
            for slug, info in self.jobs.items()
        ]

    def list_sectors(self) -> List[Dict]:
        """Liste tous les secteurs."""
        return [
            {"slug": slug, "display": info["display"], "ratio_min": info["ratio_min"], "ratio_max": info["ratio_max"]}
            for slug, info in self.sectors.items()
        ]

    def predict(
        self,
        job_slug: str,
        difficulty: str = "medium",
        experience_years: int = 0,
        location: str = "kinshasa"
    ) -> Dict:
        """
        Prédit le salaire pour un métier donné.

        Args:
            job_slug: Identifiant ASCII du métier
            difficulty: easy, medium, hard, expert
            experience_years: Années d'expérience
            location: Ville (affecte le multiplicateur géographique)

        Returns:
            Dict avec les estimations salariales
        """
        job = self.jobs.get(job_slug.lower())
        if not job:
            available = [k for k in self.jobs.keys()][:20]
            return {
                "error": f"Métier '{job_slug}' non trouvé",
                "available_jobs": available,
                "total_jobs": len(self.jobs)
            }

        sector = self.sectors[job["sector"]]
        qualification = job["qualification"]

        # Base calcul: PIB/habitant mensuel * ratio moyen du secteur
        ratio_avg = (sector["ratio_min"] + sector["ratio_max"]) / 2
        base_salary = self.gdp_monthly * ratio_avg

        # Multiplicateur qualification
        qual_mult = QUALIFICATION_MULTIPLIERS.get(qualification, 1.0)

        # Multiplicateur difficulté
        diff_mult = DIFFICULTY_MULTIPLIERS.get(difficulty, 1.0)

        # Multiplicateur expérience (+5% par année, plafonné à +50%)
        exp_mult = 1 + min(experience_years * 0.05, 0.50)

        # Multiplicateur géographique
        location_mult = self._location_multiplier(location)

        # Calcul final
        salary = base_salary * qual_mult * diff_mult * exp_mult * location_mult

        # Fourchettes
        salary_min = int(salary * 0.75)
        salary_max = int(salary * 1.25)
        salary_median = int(salary)

        # Conversion CDF
        cdf_min = salary_min * EXCHANGE_RATE_CDF
        cdf_max = salary_max * EXCHANGE_RATE_CDF
        cdf_median = salary_median * EXCHANGE_RATE_CDF

        # Conseils
        tips = NEGOTIATION_TIPS.get(job["sector"], NEGOTIATION_TIPS["default"])

        # Contexte RDC
        context = self._get_context(job["sector"], salary_median)

        return {
            "job_slug": job_slug,
            "display_name": job["display_name"],
            "sector": job["sector"],
            "display_sector": job["display_sector"],
            "qualification_level": qualification,
            "difficulty": difficulty,
            "experience_years": experience_years,
            "location": location,
            "country": "RDC",
            "currency": "USD",
            "predicted_monthly_min": salary_min,
            "predicted_monthly_max": salary_max,
            "predicted_monthly_median": salary_median,
            "in_cdf_min": cdf_min,
            "in_cdf_max": cdf_max,
            "in_cdf_median": cdf_median,
            "exchange_rate": EXCHANGE_RATE_CDF,
            "gdp_per_capita_monthly_usd": self.gdp_monthly,
            "source": "World Bank + RAID/CAJJ 2025 + ITIE RDC + OpenShores 2026",
            "last_updated": "2025-06-05",
            "negotiation_tips": tips,
            "context": context,
            "formula": {
                "base": f"{self.gdp_monthly} USD (PIB/hab mensuel) * {ratio_avg:.1f} (ratio secteur)",
                "qualification_multiplier": qual_mult,
                "difficulty_multiplier": diff_mult,
                "experience_multiplier": round(exp_mult, 2),
                "location_multiplier": location_mult
            }
        }

    def _location_multiplier(self, location: str) -> float:
        """Multiplicateur géographique."""
        multipliers = {
            "kinshasa": 1.3,
            "lubumbashi": 1.25,
            "goma": 1.15,
            "bukavu": 1.10,
            "kisangani": 1.05,
            "mbuji_mayi": 1.05,
            "kananga": 1.0,
            "kolwezi": 1.2,
            "likasi": 1.1,
            "matadi": 1.05,
            "boma": 1.0,
            "bandundu": 0.9,
            "mbandaka": 0.9,
            "province": 0.85,
            "rural": 0.75
        }
        return multipliers.get(location.lower(), 1.0)

    def _get_context(self, sector: str, salary_median: int) -> Dict:
        """Contexte comparatif pour le salaire."""
        decent_wage = 520  # RAID 2025
        national_avg = 125  # OpenShores 2026

        vs_decent = round((salary_median / decent_wage) * 100, 1)
        vs_national = round((salary_median / national_avg) * 100, 1)

        if salary_median < decent_wage:
            status = "below_decent"
            message = f"Ce salaire est inférieur au salaire décent estimé à {decent_wage} USD/mois (RAID 2025)."
        elif salary_median < decent_wage * 2:
            status = "decent"
            message = f"Ce salaire atteint le seuil du salaire décent ({decent_wage} USD/mois)."
        else:
            status = "above_decent"
            message = f"Ce salaire dépasse significativement le salaire décent."

        return {
            "vs_decent_wage_percent": vs_decent,
            "vs_national_average_percent": vs_national,
            "decent_wage_usd": decent_wage,
            "national_average_usd": national_avg,
            "status": status,
            "message": message
        }

    def compare_jobs(self, job_slug_1: str, job_slug_2: str) -> Dict:
        """Compare deux métiers."""
        pred_1 = self.predict(job_slug_1)
        pred_2 = self.predict(job_slug_2)

        if "error" in pred_1 or "error" in pred_2:
            return {"error": "Un des métiers n'a pas été trouvé"}

        diff = pred_1["predicted_monthly_median"] - pred_2["predicted_monthly_median"]

        return {
            "job_1": pred_1,
            "job_2": pred_2,
            "difference_usd": diff,
            "difference_percent": round((diff / pred_2["predicted_monthly_median"]) * 100, 1) if pred_2["predicted_monthly_median"] > 0 else 0,
            "higher_paying": job_slug_1 if diff > 0 else job_slug_2
        }


# Instance singleton
_predictor: Optional[SalaryPredictor] = None

def get_predictor() -> SalaryPredictor:
    global _predictor
    if _predictor is None:
        _predictor = SalaryPredictor()
    return _predictor