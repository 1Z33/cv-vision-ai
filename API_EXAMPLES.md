Exemples de réponses API
1. POST /api/v1/cv/analyze (Compliance)
JSON
{
  "total_score": 79.8,
  "is_compliant": true,
  "model_version": "2.0",
  "breakdown": {
    "structure": {
      "score": 90,
      "found_sections": ["header", "summary", "experience", "skills", "education"],
      "missing": []
    },
    "metrics": {
      "score": 85,
      "metrics_count": 15,
      "percentages_count": 3,
      "action_verbs": 8,
      "examples": [
        "Réduit temps de chargement de 40%",
        "Augmenté satisfaction client de 25%"
      ]
    },
    "ats": {
      "score": 75,
      "has_tables": false,
      "has_images": false,
      "issues": ["Aucun problème ATS majeur détecté"]
    },
    "keywords": {
      "score": 100,
      "matched": ["python", "javascript", "react", "node", "sql"],
      "missing": []
    },
    "length": {
      "score": 40,
      "chars": 1420,
      "pages_estimate": 0.6,
      "recommendation": "CV trop court - développez vos expériences"
    },
    "visual": {
      "verifiable": false,
      "message": "Analyse visuelle non disponible depuis le texte extrait",
      "recommendations": [
        "Utilisez une police standard (Arial, Calibri, Helvetica)",
        "Couleur principale recommandée: #1a365d",
        "Évitez les photos, tableaux, graphiques"
      ]
    }
  },
  "recommendations": [
    "📄 **Longueur**: CV trop court - développez vos expériences et compétences",
    "🎨 **Visuel**: Uploadez un PDF pour vérifier couleurs/polices"
  ],
  "priority_actions": [
    "🚨 Ajouter plus de détails dans les expériences (3-5 bullets par poste)",
    "⚠️ Enrichir le résumé avec plus de métriques chiffrées"
  ],
  "missing_elements": [],
  "forbidden_elements": []
}
```

## 2. POST /api/v1/cv/improve

```json
{
  "mode": "improve",
  "original_score": 79.8,
  "improved_score": 91.5,
  "score_improvement": 11.7,
  "model_version": "2.0",
  "formats": {
    "text": "JEAN DUPONT\n...",
    "html": "<!DOCTYPE html>...",
    "markdown": "# Jean Dupont\n..."
  },
  "improvements_applied": [
    "📄 **Longueur**: CV trop court...",
    "🎨 **Visuel**: Uploadez un PDF..."
  ],
  "remaining_issues": [
    "✅ Votre CV respecte bien le modèle universel !"
  ],
  "compliance_details": {
    "original": {"structure": 90, "metrics": 85, "ats": 75, "keywords": 100, "length": 40},
    "improved": {"structure": 95, "metrics": 95, "ats": 85, "keywords": 100, "length": 85}
  }
}
```

## 3. POST /api/v1/salary/predict

```json
{
  "job_slug": "developpeur",
  "display_name": "Développeur",
  "sector": "telecom",
  "display_sector": "Télécommunications & IT",
  "qualification_level": 3,
  "difficulty": "medium",
  "experience_years": 3,
  "location": "kinshasa",
  "country": "RDC",
  "currency": "USD",
  "predicted_monthly_min": 414,
  "predicted_monthly_max": 690,
  "predicted_monthly_median": 552,
  "in_cdf_min": 1159200,
  "in_cdf_max": 1932000,
  "in_cdf_median": 1545600,
  "exchange_rate": 2800,
  "gdp_per_capita_monthly_usd": 48,
  "source": "World Bank + RAID/CAJJ 2025 + ITIE RDC + OpenShores 2026",
  "negotiation_tips": [
    "Le secteur télécom est en forte croissance en RDC",
    "Négociez des formations certifiantes (Cisco, AWS)",
    "Le télétravail est de plus en plus accepté pour les postes IT"
  ],
  "context": {
    "vs_decent_wage_percent": 106.2,
    "vs_national_average_percent": 441.6,
    "decent_wage_usd": 520,
    "national_average_usd": 125,
    "status": "decent",
    "message": "Ce salaire atteint le seuil du salaire décent (520 USD/mois)."
  }
}