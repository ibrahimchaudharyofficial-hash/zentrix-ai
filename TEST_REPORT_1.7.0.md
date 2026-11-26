# ZENTRIX AI v1.7.0 — Test report

## Automated tests

- `python -m pytest -q`: **47 passed**.
- Includes the 43 v1.6.0 tests plus four v1.7.0 tests covering Arcade progress persistence, invalid attempt validation and offline tutor response behavior.
- `python run_100_test.py`: **100/100** benchmark questions correct, verified, with worked steps and formulas.

## Static validation

- Python compilation: `python -m py_compile backend/main.py` — passed.
- Frontend JavaScript syntax: `node --check` — passed.
- FastAPI Arcade stats/attempt and Tutor routes — exercised by TestClient tests.
- HTML source checks confirm Math Arcade, subject/difficulty controls, opt-in About setting and lazy OCR loader are present.

## Performance and environment notes

- No new frontend framework or game-engine dependency.
- Frontend HTML: approximately 85 KB; JavaScript: approximately 38 KB before compression.
- Google Fonts network requests removed; system fonts used. OCR remains lazy-loaded.
- Browser automation was attempted but loopback navigation was blocked by the execution environment. No physical test on the target laptop was performed; therefore no measured FPS, startup time or RAM claim is made.

## Scope notes

The v1.7.0 Adaptive difficulty is based on recorded Arcade accuracy, not a full student mastery model. The offline tutor is a curated topic explainer; optional Gemini explanations are not independently verified. See `V1.7.0_AUDIT.md` for limitations.
