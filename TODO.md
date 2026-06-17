# TODO

## Frontend (Vocal Interview)
- [ ] Mettre à jour `frontend/src/hooks/useVocalInterview_FINAL.ts` pour aligner:
  - champs de réponse: utiliser `next_question_text`/`next_question_number` (plat) au lieu de `data.next_question?.question_text`.
  - format d’envoi: envoyer `multipart/form-data` (FormData) avec `answer_text` et `question_number` (et `audio` si nécessaire).

## Backend (vocal-answer)
- [ ] Mettre à jour `backend/app/api/v1/interviews.py` pour aligner le handler `/vocal-answer`:
  - accepter `answer_text` et `question_number` en `Form(...)`.
  - optionnel audio STT.
  - renvoyer un format plat compatible frontend: `feedback`, `score`, `next_question_text`, `next_question_number`, etc.

## Tests
- [ ] Redémarrer backend (uvicorn --reload)
- [ ] Build frontend (npm run build)
- [ ] Tester en cliquant “Envoyer”:
  - vérifier que `POST /vocal-answer` est bien appelé
  - vérifier affichage de la prochaine question et TTS
- [ ] Vérifier logs console: `[useVocalInterview] submitAnswer` et logs backend

