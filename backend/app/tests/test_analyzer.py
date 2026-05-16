"""
Tests du moteur d'analyse de CV.
"""

import pytest
from app.services.analyzer_engine import CVAnalyzerEngine


def test_analyze_cv_with_content():
    """Test l'analyse d'un CV avec contenu."""
    engine = CVAnalyzerEngine()
    
    cv_text = """
    Jean Dupont
    Email: jean.dupont@email.com
    Téléphone: 06 12 34 56 78
    
    EXPÉRIENCE PROFESSIONNELLE
    Développeur Python chez TechCorp (2020-2024)
    - Développement d'applications web avec Django et React
    - Gestion de bases de données PostgreSQL
    - Utilisation de Docker et AWS
    
    COMPÉTENCES
    Python, Django, React, PostgreSQL, Docker, AWS, Git, Agile
    
    FORMATION
    Master Informatique - Université de Paris (2019)
    """
    
    result = engine.analyze(cv_text)
    
    assert result["overall_score"] > 0
    assert result["overall_score"] <= 100
    assert "python" in result["detected_skills"]
    assert result["contact_info_found"] is True
    assert result["sections_detected"]["experience"] is True
    assert result["sections_detected"]["skills"] is True
    assert result["sections_detected"]["education"] is True


def test_analyze_empty_cv():
    """Test l'analyse d'un CV vide."""
    engine = CVAnalyzerEngine()
    
    result = engine.analyze("")
    
    assert result["overall_score"] == 0
    assert result["detected_skills"] == []


def test_extract_skills():
    """Test l'extraction de compétences."""
    engine = CVAnalyzerEngine()
    
    text = "Je maîtrise Python, React, Docker et AWS"
    skills = engine._extract_skills(text)
    
    assert "python" in skills
    assert "react" in skills
    assert "docker" in skills
    assert "aws" in skills