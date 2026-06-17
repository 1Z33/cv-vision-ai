# TODO - Fix Production Gemini-only WS stability

- [ ] Inspect current WS + vocal interview endpoints for UUID handling and fallback generation paths.
- [ ] Fix UUID type errors: ensure every db.get(InterviewSessionModel, ...) receives a UUID instance.
- [ ] Remove/disable local vocal-question fallbacks (generate_vocal_question and any other fallback question code paths) to enforce Gemini-only.
- [ ] Adjust Gemini error handling: on quota errors emit only `event=quota_exceeded` and stop; on other Gemini errors emit only `event=error` with the required message.
- [ ] Ensure no `next_question` events are emitted in WS flow; only `question` event.
- [ ] Add/adjust unit tests to lock: quota error path + UUID conversion path + no fallback path.

