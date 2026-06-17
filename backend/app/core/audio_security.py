"""Sécurité audio (validation upload, limites, MIME).

Centralise les validations requises par les endpoints d'entretien vocal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import UploadFile, HTTPException


@dataclass(frozen=True)
class AudioValidationResult:
    filename: str
    content_type: str
    size_bytes: int


# Basé sur des formats utilisés par le front (WebM/Opus) ou conversion côté serveur.
DEFAULT_ALLOWED_MIME_TYPES = {
    "audio/webm",
    "audio/webm;codecs=opus",
    "audio/ogg",
    "audio/ogg;codecs=opus",
    "audio/opus",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/x-m4a",
    "audio/wav",
    "audio/flac",
}


def _guess_mime_type(upload: UploadFile) -> str:
    return (upload.content_type or "").strip().lower()


async def validate_audio_upload(
    audio: UploadFile,
    *,
    max_size_bytes: int = 10 * 1024 * 1024,
    allowed_mime_types: Optional[set[str]] = None,
) -> AudioValidationResult:
    """Valide un upload audio.

    - Limite taille
    - Vérifie MIME content-type

    Important : la validation taille/MIME peut nécessiter de lire le fichier.
    Ici on lit uniquement la taille via seek/tell; si le stream ne le permet pas,
    l'appelant doit gérer.
    """

    allowed_mime_types = allowed_mime_types or DEFAULT_ALLOWED_MIME_TYPES

    filename = audio.filename or "audio"
    content_type = _guess_mime_type(audio)

    if content_type and content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=415,
            detail=f"Type MIME non supporté: {content_type}",
        )

    # Tenter de mesurer la taille sans casser le stream.
    size_bytes = 0
    try:
        # Starlette UploadFile est un SpooledTemporaryFile, seek/tell OK.
        audio.file.seek(0, 2)  # end
        size_bytes = audio.file.tell()
        audio.file.seek(0)
    except Exception:
        # fallback: lecture complète (moins optimal, mais protège la prod)
        content = await audio.read()
        size_bytes = len(content)
        # remettre le curseur à 0 en recréant un buffer via UploadFile n'est pas trivial.
        # Dans ce projet, on privilégie la conversion côté VocalService qui relit le fichier.
        # Ici, on conserve le contenu dans le stream en réécrivant.
        audio.file.seek(0)

    if size_bytes > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier audio trop volumineux (max {max_size_bytes // (1024 * 1024)}MB).",
        )

    return AudioValidationResult(
        filename=filename,
        content_type=content_type or "application/octet-stream",
        size_bytes=size_bytes,
    )

