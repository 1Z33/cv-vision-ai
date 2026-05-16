"""
Point d'entrée principal de l'application FastAPI.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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

# CORS - Autoriser le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite / React dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# ROUTES
# ============================================
app.include_router(api_router)

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