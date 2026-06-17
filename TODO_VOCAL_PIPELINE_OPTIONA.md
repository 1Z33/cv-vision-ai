# TODO - Fix pipeline vocal instable (Option A)

## Frontend
- [ ] Remplacer `frontend/src/hooks/useVocalInterview_FINAL.ts` par la version “Option A” (envoi JSON answer_text, pas d’audio).
- [ ] Remplacer `frontend/src/components/VocalInterview.tsx` pour ne plus utiliser `useAudioRecorder` et pour n’envoyer que la transcription.

## Backend
- [ ] Ajouter/modifier l’endpoint `/{session_id}/vocal-answer` (ou un nouvel endpoint) pour accepter JSON `answer_text` + `question_number`.
- [ ] S’assurer que la logique d’évaluation appelle directement `evaluate_vocal_answer` (ou l’équivalent) avec `answer_text`.

## Validation
- [ ] Relancer le build frontend.
- [ ] Tester manuellement 3–5 interviews vocales : vérifier `answer_transcription`/scoring non vides et cohérents.
