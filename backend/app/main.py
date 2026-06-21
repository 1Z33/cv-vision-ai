"""
Point d'entrée principal de l'application FastAPI.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse


from app.core.config import settings
from app.core.logging import logger
from app.api.api import api_router

# ============================================
# LIFESPAN (Startup & Shutdown)
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application."""
    logger.info("🚀 CVision AI API en cours de démarrage...")
    logger.info(f"Environnement: {settings.ENVIRONMENT}")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    logger.info("👋 CVision AI API en cours d'arrêt...")

# ============================================
# CRÉATION DE L'APPLICATION
# ============================================
app = FastAPI(
    title="CVision AI API",
    description="API d'analyse de CV et préparation aux entretiens par IA",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# ============================================
# MIDDLEWARES
# ============================================

# CORS - Configuration pour développement et production
# En développement: localhost:5173 et localhost:3000
# En production: domaine réel du frontend (Render)
allowed_origins = [
    "http://localhost:5173",  # Vite dev
    "https://cv-vision-ai-8.onrender.com",  # Frontend Render (production)
]



app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip - Compression des réponses (avant les routes)
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compresse si réponse > 1KB

# ============================================
# ROUTES
# ============================================
app.include_router(api_router)

# Servir les fichiers audio générés
from fastapi.staticfiles import StaticFiles

uploads_audio_dir = os.path.join(settings.UPLOAD_DIR, "audio")
os.makedirs(uploads_audio_dir, exist_ok=True)
app.mount("/uploads/audio", StaticFiles(directory=uploads_audio_dir), name="audio")


# ============================================
# GESTION DES EXCEPTIONS
# ============================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Capture toutes les erreurs non gérées pour éviter de crash proprement."""
    logger.error(f"Erreur non gérée sur {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Une erreur interne est survenue.",
            "type": exc.__class__.__name__
        }
    )

# ============================================
# HEALTH CHECK
# ============================================
@app.get("/health")
async def health_check():
    """Endpoint de vérification de santé."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    """Page d'accueil de l'API."""
    return {
        "message": "Bienvenue sur CVision AI API",
        "documentation": "/docs",
        "version": "1.0.0"
    }