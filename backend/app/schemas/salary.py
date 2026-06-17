"""
Schémas Pydantic pour le Salary Predictor et le CV Model Analyzer
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum


# ============= SALARY PREDICTOR =============

class DifficultyLevel(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"
    expert = "expert"


class LocationRDC(str, Enum):
    kinshasa = "kinshasa"
    lubumbashi = "lubumbashi"
    goma = "goma"
    bukavu = "bukavu"
    kisangani = "kisangani"
    mbuji_mayi = "mbuji_mayi"
    kananga = "kananga"
    kolwezi = "kolwezi"
    likasi = "likasi"
    matadi = "matadi"
    boma = "boma"
    bandundu = "bandundu"
    mbandaka = "mbandaka"
    province = "province"
    rural = "rural"


class SalaryPredictRequest(BaseModel):
    job_slug: str = Field(..., description="Identifiant ASCII du métier (ex: developpeur)")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.medium, description="Niveau de difficulté de l'entretien")
    experience_years: int = Field(default=0, ge=0, le=50, description="Années d'expérience")
    location: LocationRDC = Field(default=LocationRDC.kinshasa, description="Ville/localisation")


class SalaryContext(BaseModel):
    vs_decent_wage_percent: float
    vs_national_average_percent: float
    decent_wage_usd: int
    national_average_usd: int
    status: str
    message: str


class SalaryFormula(BaseModel):
    base: str
    qualification_multiplier: float
    difficulty_multiplier: float
    experience_multiplier: float
    location_multiplier: float


class SalaryPredictResponse(BaseModel):
    job_slug: str
    display_name: str
    sector: str
    display_sector: str
    qualification_level: int
    difficulty: str
    experience_years: int
    location: str
    country: str
    currency: str
    predicted_monthly_min: int
    predicted_monthly_max: int
    predicted_monthly_median: int
    in_cdf_min: int
    in_cdf_max: int
    in_cdf_median: int
    exchange_rate: int
    gdp_per_capita_monthly_usd: int
    source: str
    last_updated: str
    negotiation_tips: List[str]
    context: SalaryContext
    formula: SalaryFormula


class JobListItem(BaseModel):
    slug: str
    display_name: str
    sector: str
    display_sector: str
    qualification: int


class JobListResponse(BaseModel):
    total: int
    jobs: List[JobListItem]


class SectorListItem(BaseModel):
    slug: str
    display: str
    ratio_min: float
    ratio_max: float


class SectorListResponse(BaseModel):
    total: int
    sectors: List[SectorListItem]


class JobCompareRequest(BaseModel):
    job_slug_1: str
    job_slug_2: str


class JobCompareResponse(BaseModel):
    job_1: SalaryPredictResponse
    job_2: SalaryPredictResponse
    difference_usd: int
    difference_percent: float
    higher_paying: str


# ============= CV MODEL ANALYZER =============

class CVAnalysisMode(str, Enum):
    analyze_only = "analyze_only"      # Analyse seule
    improve = "improve"                 # Analyse + suggestions d'amélioration
    generate = "generate"              # Analyse + génération CV optimisé


class CVUploadRequest(BaseModel):
    job_title: str = Field(..., description="Titre du poste visé")
    mode: CVAnalysisMode = Field(default=CVAnalysisMode.analyze_only)
    language: str = Field(default="fr", description="Langue du CV (fr, en)")


class CVSectionScore(BaseModel):
    section: str
    score: float = Field(..., ge=0, le=100)
    max_score: float
    feedback: str
    suggestions: List[str]


class CVVisualScore(BaseModel):
    score: float = Field(..., ge=0, le=100)
    layout: str
    colors: str
    fonts: str
    spacing: str
    issues: List[str]
    recommendations: List[str]


class CVATSAnalysis(BaseModel):
    score: float = Field(..., ge=0, le=100)
    file_format: str
    has_tables: bool
    has_images: bool
    has_graphics: bool
    standard_fonts: bool
    keyword_density: float
    issues: List[str]


class CVMetricsAnalysis(BaseModel):
    score: float = Field(..., ge=0, le=100)
    metrics_count: int
    metrics_ratio: float
    action_verbs_count: int
    weak_verbs_count: int
    examples: List[str]


class CVKeywordAnalysis(BaseModel):
    score: float = Field(..., ge=0, le=100)
    matched_keywords: List[str]
    missing_keywords: List[str]
    keyword_density: float


class CVLengthAnalysis(BaseModel):
    score: float = Field(..., ge=0, le=100)
    current_length_chars: int
    recommended_max: int
    current_pages_estimate: float
    recommendation: str


class CVAnalysisResponse(BaseModel):
    total_score: float = Field(..., ge=0, le=100)
    model_version: str
    mode: str

    # Scores détaillés
    structure_score: CVSectionScore
    metrics_score: CVMetricsAnalysis
    ats_score: CVATSAnalysis
    keywords_score: CVKeywordAnalysis
    length_score: CVLengthAnalysis
    visual_score: Optional[CVVisualScore] = None

    # Recommandations
    recommendations: List[str]
    priority_actions: List[str]

    # Comparaison au modèle
    model_compliance_percent: float
    missing_elements: List[str]

    # Génération (si mode = generate)
    generated_cv: Optional[str] = None
    generated_cv_html: Optional[str] = None


class CVGenerateRequest(BaseModel):
    user_data: Dict[str, Any] = Field(..., description="Données utilisateur (nom, expérience, compétences, etc.)")
    job_title: str = Field(..., description="Titre du poste visé")
    output_format: str = Field(default="html", description="html, pdf, markdown")
    language: str = Field(default="fr")


class CVGenerateResponse(BaseModel):
    cv_text: str
    cv_html: Optional[str] = None
    cv_pdf_url: Optional[str] = None
    ats_score: float
    recommendations: List[str]


class CVModelReference(BaseModel):
    model_name: str
    version: str
    based_on: List[str]
    structure: Dict[str, Any]
    visual_design: Dict[str, Any]
    ats_compatibility: Dict[str, Any]
    scoring_global: Dict[str, Any]