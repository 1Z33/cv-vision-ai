import asyncio
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_ws_quota_exceeded_emits_only_quota_exceeded_and_error_not_emitted(monkeypatch):
    """Regression test for Gemini-only contract.

    Goal: when Gemini raises quota-like error, WS must emit event `quota_exceeded`
    and must NOT emit a replacement `question`.

    Note: this test is a unit-level contract test; it stubs the websocket and
    GeminiService.
    """

    # Local import to avoid side effects during collection
    from app.api.v1.interview_live_ws import interview_live_ws

    emitted = []

    class DummyWS:
        def __init__(self, session_id: str):
            self.session_id = session_id
            self._received = [
                {"event": "heartbeat", "payload": {}},
            ]

        async def accept(self):
            return

        async def send_json(self, msg):
            emitted.append(msg)

        async def receive_json(self):
            # First call after startup will block; we stop by raising disconnect.
            raise RuntimeError("stop")

        async def close(self, code=None):
            return

    # --- Patch dependencies ---
    # get_db async generator
    async def fake_get_db_gen():
        class FakeDB:
            async def __anext__(self):
                return self

        return FakeDB()

    # Better: override get_db() to return an async generator object with __anext__.
    from app import api

    # Stub GeminiService
    class FakeGeminiService:
        async def generate_next_question(self, *args, **kwargs):
            raise RuntimeError("429 RESOURCE_EXHAUSTED: quota exceeded")

    # Stub VocalService TTS to ensure it is never called in quota path
    class FakeVocalService:
        async def text_to_speech(self, *args, **kwargs):
            raise AssertionError("TTS should not be called on quota")

    session_uuid = uuid4()
    ws = DummyWS(str(session_uuid))

    # Monkeypatch in module namespace
    import app.api.v1.interview_live_ws as ws_module

    # Replace GeminiService/VocalService in module
    monkeypatch.setattr(ws_module, "GeminiService", FakeGeminiService)
    monkeypatch.setattr(ws_module, "VocalService", FakeVocalService)

    # Replace get_db dependency generator
    class DummyDB:
        async def get(self, *args, **kwargs):
            return None

        async def execute(self, *args, **kwargs):
            class R:
                def scalars(self):
                    return self

                def first(self):
                    return None

                def scalar_one_or_none(self):
                    return None

            return R()

        async def close(self):
            return

    async def dummy_anext():
        return DummyDB()

    class DummyDBGen:
        def __init__(self):
            self.called = 0

        async def __anext__(self):
            self.called += 1
            return DummyDB()

    monkeypatch.setattr(ws_module, "get_db", lambda: DummyDBGen())

    # Replace get_current_user to force current_user = None
    async def fake_get_current_user(ws_obj):
        raise RuntimeError("auth disabled")

    monkeypatch.setattr(ws_module, "get_current_user", fake_get_current_user)

    with pytest.raises(RuntimeError):
        await interview_live_ws(ws, str(session_uuid))

    # Validate emitted contract
    events = [m["event"] for m in emitted if isinstance(m, dict)]

    assert "quota_exceeded" in events
    assert "question" not in events
    # `error` may be emitted only in non-quota cases; enforce strictness for this test.
    assert "error" not in events

