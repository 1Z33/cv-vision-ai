import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile


# Dossier pour stocker les fichiers audio générés/transformés
AUDIO_DIR = Path("uploads/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class VocalService:
    """STT (audio -> texte) + TTS (texte -> audio).

    Implémentation STT via SpeechRecognition (Google Speech API).
    Implémentation TTS via gTTS (Google Text-to-Speech).

    Notes:
    - STT dépend d'Internet (API Google).
    - SpeechRecognition dépend du format exact du fichier audio.

    Pour stabiliser le pipeline, on convertit systématiquement l'audio uploadé en WAV
    (via ffmpeg si disponible) avant d'appeler sr.AudioFile().
    """

    def __init__(self):
        import speech_recognition as sr

        self._sr = sr
        self._recognizer = sr.Recognizer()

    async def speech_to_text(self, audio_file: UploadFile) -> str:
        """Convertit un fichier audio en texte (STT).

        Objectif:
        - ne jamais faire crasher le endpoint (conversion + erreurs de décodage gérées)
        - rendre compatible avec sr.AudioFile() en convertissant vers WAV 16kHz mono
        """
        # Import local pour éviter d'alourdir le chargement
        sr = self._sr

        content = await audio_file.read()

        # Sauvegarde temporaire
        original_suffix = Path(audio_file.filename or "").suffix.lower()
        if original_suffix not in {".wav", ".mp3", ".ogg", ".m4a", ".flac", ".webm"}:
            original_suffix = ".webm"

        input_name = f"stt_in_{uuid.uuid4()}{original_suffix}"
        input_path = AUDIO_DIR / input_name

        wav_name = f"stt_out_{uuid.uuid4()}.wav"
        wav_path = AUDIO_DIR / wav_name

        try:
            input_path.write_bytes(content)

            # Conversion WAV via ffmpeg si disponible
            # (si ffmpeg absent ou conversion impossible, on tente quand même le décodage direct)
            used_path = input_path
            try:
                import subprocess

                ffmpeg_cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(input_path),
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    "-f",
                    "wav",
                    str(wav_path),
                ]
                subprocess.run(ffmpeg_cmd, check=True, capture_output=True, timeout=20)
                used_path = wav_path
            except Exception:
                # ffmpeg non dispo / conversion échouée
                used_path = input_path

            # SpeechRecognition attend un fichier disque
            try:
                with sr.AudioFile(str(used_path)) as source:
                    audio_data = self._recognizer.record(source)
            except Exception:
                # Type de décodage non supporté
                return ""

            try:
                text = self._recognizer.recognize_google(audio_data, language="fr-FR")
                return text or ""
            except sr.UnknownValueError:
                return ""
            except sr.RequestError:
                return ""

        finally:
            for p in (input_path, wav_path):
                try:
                    if p.exists():
                        p.unlink()
                except Exception:
                    pass


    async def text_to_speech(self, text: str) -> Optional[str]:
        """Convertit un texte en audio et retourne l'URL relative.

        Implémentation offline: pyttsx3.
        Si pyttsx3 n'est pas disponible, renvoie None (plutôt que 500).
        """
        if not text or not text.strip():
            return None

        try:
            import pyttsx3
        except Exception:
            return None

        filename = f"tts_{uuid.uuid4()}.mp3"
        filepath = AUDIO_DIR / filename

        try:
            # pyttsx3 n'écrit pas forcément en mp3 selon l'OS/driver.
            # Comme le front attend une URL, on tente tout de même.
            engine = pyttsx3.init()
            engine.save_to_file(text, str(filepath))
            engine.runAndWait()
            return f"/uploads/audio/{filename}"
        except Exception:
            return None


def cleanup_old_audio(max_age_hours: int = 24):
    """Optionnel: nettoyage des fichiers audio. Non appelé automatiquement."""
    import time

    now = time.time()
    cutoff = now - max_age_hours * 3600

    if not AUDIO_DIR.exists():
        return

    for p in AUDIO_DIR.glob("*"):
        try:
            if p.is_file() and p.stat().st_mtime < cutoff:
                p.unlink()
        except Exception:
            pass

