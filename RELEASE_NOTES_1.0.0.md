# Zentrix AI 1.0.0 — Workspace redesign

## Interface
- Rebuilt the workspace around a calmer pastel lavender, blue, and mint design system.
- Added responsive collapsible navigation, clear page destinations, and a compact command palette (Ctrl+K).
- Added guided math starters and a focused solver composer with keyboard submission.
- Added a dedicated Matrix Lab for entering A and B and choosing addition, subtraction, or multiplication.
- Improved solution presentation with separate Steps, Verification, and Formula tabs; copy and print actions.
- Added searchable browser-local history, clear-history action, responsive graph controls, and light/dark theme persistence.
- Preserved the existing welcome image and author identity.

## Mathematics
- Added local named-matrix parsing: define A and B on separate lines, then enter `find A-B`, `find A+B`, or `find A*B`. This does not require Gemini.
- Added matrix transpose support.
- Added regression coverage for named matrix subtraction and transpose.

## Reliability and security
- Gemini key verification now happens before writing the key to `.env`. Invalid or unreachable keys are not persisted by the settings endpoint.
- Existing local math functionality remains available when Gemini is not configured.
- Preserved browser-local calculation history and migrated the older `zx` history key when no new history exists.

## Validation
- Core engine: 40/40 regression cases passed.
- Punjab Class 10 benchmark: 22/22 passed.
- Cross-grade curriculum benchmark: 38/38 passed.
- Expanded school mathematics benchmark: 28/28 passed.
- FastAPI smoke tests: health, solve endpoints, root page, and welcome image returned HTTP 200.
- Inline JavaScript syntax check passed with Node.js.

These are finite regression tests, not proof of complete coverage for every mathematical problem or textbook. Gemini live connectivity still requires a valid user-provided API key and is subject to Google's quota and model availability.
