# Zentrix AI 1.0.1 — Gemini connection fix

- Fixed an overly restrictive API-key character check that could reject valid Google AI Studio keys.
- Zentrix now validates key length and printable characters, then lets Google's Gemini API verify whether the key is active and authorized.
- Keys are still saved locally only after Google confirms the connection.
- Kept the current `gemini-3.5-flash-lite` model default.
- No OpenAI API or paid provider is required.
