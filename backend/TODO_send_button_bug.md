# Bug: bouton « Envoyer » ne marche pas (Entretien vocal)

## Analyse effectuée (front)
- Le composant `VocalInterview.tsx` ne rend le bouton **Envoyer** que si `transcript.trim() && !isListening`.
- Le handler `handleSubmit` appelle `submitAnswer(sessionId, currentQuestionNumber)`.

## Cause probable (backend / API mismatch)
- `VocalInterview.tsx` utilise le hook `useVocalInterview_FINAL.ts`.
- Dans `useVocalInterview_FINAL.ts`, `submitAnswer()` envoie vers `POST /api/v1/interviews/{sessionId}/vocal-answer` avec un **FormData**:
  - `answer_text`
  - `question_number`

## Cause probable (routing / auth / payload)
- Le backend (FastAPI) n’attend pas `answer_text` comme JSON mais comme `Form(None)` appelé `answer_text` (OK), toutefois le endpoint renvoie un schéma différent de ce que le hook consomme.
- Point critique: backend renvoie `next_question_text/next_question_audio_url`, mais le hook lit `data.next_question?.question_text` et `data.next_question_number`.

## Plan correctif
1. Mettre à jour `useVocalInterview_FINAL.ts` pour mapper correctement la réponse backend:
   - `currentQuestion` ← `data.next_question_text`
   - `currentQuestionNumber` ← `questionNumber + 1` (ou calcul via renvoi si disponible)
   - `feedback` ← `data.feedback_text` ou `data.feedback_text`/`data.evaluation?.feedback`
2. Ajouter un `catch` qui log `response.status` + `await response.text()` quand `!response.ok` pour diagnostiquer rapidement.
3. Optionnel: corriger le conditionnement du bouton (rendre disabled au lieu de ne pas afficher) pour éviter les cas où `transcript` reste vide.

## Étapes de vérification
- Tester vocal:
  - parler => voir transcript
  - bouton Envoyer apparaît
  - cliquer => vérifier que POST retourne 2xx
  - vérifier que next question s’affiche et que la boucle continue

