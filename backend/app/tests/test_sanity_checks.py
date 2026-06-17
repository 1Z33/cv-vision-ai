"""
Tests de validation pour le Salary Predictor et CV Model Analyzer
"""

import json
import sys
from pathlib import Path

# Ajouter le backend au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.salary_predictor import SalaryPredictor
from app.services.model_analyser import CVModelAnalyzer
from app.services.salary_predictor import CVGenerator


def test_salary_predictor():
    """Test le Salary Predictor."""
    print("\n" + "="*60)
    print("🧪 TEST: Salary Predictor RDC")
    print("="*60)

    predictor = SalaryPredictor()

    # Test 1: Liste des métiers
    jobs = predictor.list_jobs()
    print(f"\n✅ Total métiers: {len(jobs)}")
    assert len(jobs) >= 200, f"ATTENDU: 200+ métiers, TROUVÉ: {len(jobs)}"

    # Test 2: Liste des secteurs
    sectors = predictor.list_sectors()
    print(f"✅ Total secteurs: {len(sectors)}")
    assert len(sectors) == 20, f"ATTENDU: 20 secteurs, TROUVÉ: {len(sectors)}"

    # Test 3: Prédiction pour un développeur
    result = predictor.predict("developpeur", "medium", 3, "kinshasa")
    print(f"\n📊 Développeur (3 ans, Kinshasa):")
    print(f"   Min: {result['predicted_monthly_min']} USD")
    print(f"   Max: {result['predicted_monthly_max']} USD")
    print(f"   Médiane: {result.get('predicted_monthly_median', result.get('predicted_monthly_median_usd', 'N/A'))} USD")
    print(f"   En CDF: {result['in_cdf_median']:,} CDF")

    print(f"   Contexte: {result['context']['message']}")
    assert "error" not in result, f"ERREUR: {result.get('error')}"
    assert result["predicted_monthly_median"] > 0

    # Test 4: Prédiction pour un médecin
    result = predictor.predict("medecin", "hard", 5, "lubumbashi")
    print(f"\n📊 Médecin (5 ans, Lubumbashi):")
    print(f"   Médiane: {result.get('predicted_monthly_median', result.get('predicted_monthly_median_usd', 'N/A'))} USD")

    print(f"   En CDF: {result['in_cdf_median']:,} CDF")
    assert result.get("predicted_monthly_median", 0) > 200


    # Test 5: Comparaison
    comparison = predictor.compare_jobs("developpeur", "medecin")
    print(f"\n📊 Comparaison Développeur vs Médecin:")
    print(f"   Différence: {comparison['difference_usd']} USD")
    print(f"   Mieux payé: {comparison['higher_paying']}")

    # Test 6: Métier inconnu
    result = predictor.predict("metier_inexistant")
    print(f"\n📊 Métier inexistant:")
    print(f"   Erreur: {result['error']}")
    assert "error" in result

    print("\n✅ Tous les tests Salary Predictor PASSÉS!")
    return True


def test_cv_analyzer():
    """Test le CV Model Analyzer."""
    print("\n" + "="*60)
    print("🧪 TEST: CV Model Analyzer")
    print("="*60)

    analyzer = CVModelAnalyzer()

    # CV de test
    cv_test = """
    JEAN DUPONT
    jean.dupont@email.com | +243 81 234 5678 | Kinshasa, RDC

    RÉSUMÉ PROFESSIONNEL
    Développeur Full-Stack avec 5 ans d'expérience. Spécialisé React/Node.js.
    Réduit temps de chargement de 40% chez TechCorp. Augmenté satisfaction client de 25%.
    À la recherche d'un poste Lead Developer.

    EXPÉRIENCE PROFESSIONNELLE

    Développeur Senior | TechCorp RDC
    01/2022 - Présent | Kinshasa
    • Développé une application web utilisée par 10 000+ utilisateurs
    • Réduit le temps de chargement de 40% en optimisant les requêtes SQL
    • Formé une équipe de 3 développeurs juniors
    • Implémenté un système CI/CD réduisant les déploiements de 50%
    • Conçu l'architecture microservices de la plateforme

    Développeur Full-Stack | StartupXYZ
    06/2020 - 12/2021 | Kinshasa
    • Créé le MVP de l'application en 3 mois
    • Augmenté les conversions de 30% avec l'A/B testing
    • Géré le passage de 100 à 5000 utilisateurs actifs

    COMPÉTENCES
    Python, JavaScript, React, Node.js, PostgreSQL, Docker, AWS, Git

    FORMATION
    Licence Informatique - Université de Kinshasa (UNIKIN) | 2020
    """

    # Test analyse
    result = analyzer.analyze(cv_test, "Développeur Full-Stack", "analyze_only")
    print(f"\n📊 Score total: {result['total_score']}/100")
    print(f"📊 Score structure: {result['structure_score']['score']}/100")
    print(f"📊 Score métriques: {result['metrics_score']['score']}/100")
    print(f"📊 Score ATS: {result['ats_score']['score']}/100")
    print(f"📊 Score mots-clés: {result['keywords_score']['score']}/100")
    print(f"📊 Score longueur: {result['length_score']['score']}/100")
    print(f"\n📋 Recommandations:")
    for rec in result['recommendations'][:3]:
        print(f"   • {rec}")

    assert result["total_score"] > 0
    assert len(result["recommendations"]) > 0

    print("\n✅ Tous les tests CV Analyzer PASSÉS!")
    return True


def test_cv_generator():
    """Test le CV Generator."""
    print("\n" + "="*60)
    print("🧪 TEST: CV Generator")
    print("="*60)

    generator = CVGenerator()

    user_data = {
        "name": "Jean Dupont",
        "email": "jean.dupont@email.com",
        "phone": "+243 81 234 5678",
        "location": "Kinshasa, RDC",
        "linkedin": "linkedin.com/in/jeandupont",
        "experience": [
            {
                "title": "Développeur Senior",
                "company": "TechCorp RDC",
                "dates": "01/2022 - Présent",
                "location": "Kinshasa",
                "bullets": [
                    "Développé une application web utilisée par 10 000+ utilisateurs",
                    "Réduit le temps de chargement de 40%",
                    "Formé une équipe de 3 développeurs"
                ]
            },
            {
                "title": "Développeur Full-Stack",
                "company": "StartupXYZ",
                "dates": "06/2020 - 12/2021",
                "location": "Kinshasa",
                "bullets": [
                    "Créé le MVP en 3 mois",
                    "Augmenté les conversions de 30%"
                ]
            }
        ],
        "skills": ["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Docker"],
        "education": [
            {"degree": "Licence Informatique", "school": "UNIKIN", "year": "2020"}
        ]
    }

    # Test génération
    result = generator.generate(user_data, "Développeur Full-Stack", "all", "fr")
    print(f"\n📄 CV généré:")
    print(f"   Format texte: {len(result['text'])} caractères")
    print(f"   Format HTML: {len(result['html'])} caractères")
    print(f"   Format Markdown: {len(result['markdown'])} caractères")
    print(f"   Score ATS estimé: {result['estimated_ats_score']}/100")

    assert "text" in result
    assert "html" in result
    assert "markdown" in result

    # Afficher un aperçu
    print(f"\n📋 Aperçu (texte):")
    print("-" * 40)
    print(result["text"][:500])
    print("...")

    print("\n✅ Tous les tests CV Generator PASSÉS!")
    return True


def test_data_files():
    """Vérifie les fichiers de données."""
    print("\n" + "="*60)
    print("🧪 TEST: Fichiers de données")
    print("="*60)

    base_dir = Path(__file__).parent.parent / "data"

    # jobs_rdc.json
    jobs_file = base_dir / "jobs_rdc.json"
    assert jobs_file.exists(), f"Fichier manquant: {jobs_file}"
    with open(jobs_file, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    print(f"✅ jobs_rdc.json: {len(jobs['jobs'])} métiers, {len(jobs['sectors'])} secteurs")
    assert len(jobs["jobs"]) >= 200

    # cv_model_universal.json
    model_file = base_dir / "cv_model_universal.json"
    assert model_file.exists(), f"Fichier manquant: {model_file}"
    with open(model_file, "r", encoding="utf-8") as f:
        model = json.load(f)
    print(f"✅ cv_model_universal.json: version {model['version']}")
    assert "structure" in model
    assert "visual_design" in model

    print("\n✅ Tous les tests de données PASSÉS!")
    return True


if __name__ == "__main__":
    print("\n" + "🚀"*30)
    print("   CVISION AI - SUITE DE TESTS COMPLETE")
    print("🚀"*30)

    try:
        test_data_files()
        test_salary_predictor()
        test_cv_analyzer()
        test_cv_generator()

        print("\n" + "🎉"*30)
        print("   TOUS LES TESTS SONT PASSÉS!")
        print("🎉"*30)

    except Exception as e:
        print(f"\n❌ TEST ÉCHOUÉ: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
