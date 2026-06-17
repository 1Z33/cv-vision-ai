# TODO_LIVE_WEBSOCKET_V2 (Phase suivante : intégration complète Live Interview)

## 1) Backend — WebSocket only
- [ ] Ajouter un WebSocket FastAPI `/api/v1/interview/live/{session_id}`.
- [ ] Implémenter protocole event/payload (session_started, question, transcript, analysis_update, analysis, next_question, session_finished, error).
- [ ] Valider session_id et ownership utilisateur (ou fallback si non disponible).
- [ ] À la connexion: envoyer `session_started` puis la première `question` automatiquement.

## 2) Backend — Microphone streaming V2
- [ ] Créer `SpeechService.stream_audio()` (ou équivalent) : recevoir `audio_chunk` base64 -> bytes.
- [ ] Créer `SpeechService.transcribe_stream()` : produire transcription progressive.
- [ ] Recalculer/flush transcript quand assez de données.

## 3) Backend — Analyse progressive
- [ ] Wire Gemini/InterviewService pour envoyer `analysis_update` pendant la génération/évaluation.
- [ ] Envoyer `analysis` finale ensuite.
- [ ] Déclencher `next_question` puis `session_finished` à la fin.

## 4) Backend — Gemini Live Ready (architecture)
- [ ] Préparer une interface compatible Gemini Live: `GeminiService.stream_response()`.
- [ ] Préparer l’orchestrateur live (audio->STT->Gemini->events).

## 5) Frontend — Microphone streaming + WebSocket events
- [ ] Brancher `MediaRecorder` => chunks => `audio_chunk` WS.
- [ ] Mettre à jour `useWebSocketInterview` pour gérer `transcript` et `analysis_update`.
- [ ] Ajouter écoute `error` plus détaillée.

## 6) Frontend — UI temps réel
- [ ] Animation avatar IA quand IA parle.
- [ ] Animation microphone quand utilisateur parle.
- [ ] Visualiseur audio (AnalyserNode) lié aux chunks ou au niveau micro.
- [ ] Historique conversation enrichi (transcript + analysis_update).

## 7) Validation finale (sans endpoints HTTP)
- [ ] Connexion WS -> `session_started`.
- [ ] Réception `question`.
- [ ] Lecture audio.
- [ ] Microphone actif -> envoi `audio_chunk`.
- [ ] Réception `transcript` progressive.
- [ ] Réception `analysis_update` avant `analysis`.
- [ ] Réception `next_question`.
- [ ] Réception `session_finished`.

