from google import genai

import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

if not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError("Missing GEMINI_API_KEY env var (set in backend/.env or your shell)")

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Dis simplement Bonjour"
)

print(response.text)