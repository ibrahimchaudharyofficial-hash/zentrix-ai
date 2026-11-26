# Zentrix AI v0.9.0 — Gemini integration and matrix operations

- Added optional Google Gemini API integration for natural-language-to-command translation.
- Gemini is called only after the local parser cannot interpret a request; SymPy remains the calculation engine.
- API key is loaded server-side from the project-root `.env`; it is not exposed to the browser.
- Added matrix addition, subtraction, and multiplication with exact SymPy results and independent NumPy checks where numeric.
- Added a free-tier Gemini setup guide and updated the health endpoint to report provider configuration.
- Added regression tests for matrix addition, subtraction, and multiplication.
- No API key is included in this release archive. Configure your own key locally.
