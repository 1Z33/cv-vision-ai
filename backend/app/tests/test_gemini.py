"""Gemini integration smoke test.

NOTE: This test is intentionally marked as xfail by default because it calls the
real Gemini API during execution. If you want it to run, export
RUN_GEMINI_INTEGRATION_TESTS=1 and ensure you have sufficient quota.

IMPORTANT: No network calls should happen at import time (pytest collection).
"""

import os

import pytest



@pytest.mark.xfail(
    reason="Requires real Gemini API quota; mark RUN_GEMINI_INTEGRATION_TESTS=1 to enable.",
    strict=False,
)
def test_gemini_smoke() -> None:
    # Local import to avoid side effects during collection
    from google import genai

    import os

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY env var (set in backend/.env or your shell)")

    client = genai.Client(api_key=api_key)

    # Allow opt-in for real quota tests
    if os.getenv("RUN_GEMINI_INTEGRATION_TESTS") != "1":
        pytest.xfail("RUN_GEMINI_INTEGRATION_TESTS not set")

    response = client.models.generate_content(
        model="gemini-1.5-flash-8b",
        contents="Dis simplement Bonjour",
    )

    assert getattr(response, "text", None) is not None

