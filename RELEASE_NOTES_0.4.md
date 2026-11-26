# Zentrix AI 0.4.0 — Engine Expansion

## New mathematical operations
- Real one-variable inequality solving: `solve x^2 < 4`
- Partial derivatives: `partial derivative of x^2*y + sin(y) with respect to x`
- Taylor series: `series sin(x) around x=0 to 7` (order 1–30)
- Finite summations: `sum k^2 from k=1 to 10`

## Platform changes
- Added `/api/capabilities` endpoint.
- Updated app version to 0.4.0.
- Added dashboard quick-start examples for the new operations.
- Expanded regression suite from 33 to 37 mathematical cases.

## Verification performed for this release
- 37/37 mathematical regression cases passed.
- FastAPI TestClient smoke checks passed for health, capabilities, and all four new operations.
- Linear equation smoke test `3x=21` returned 7.

## Notes
This remains an early-stage local mathematical application. These additions do not make it a universal or research-proven CAS. Numerical checks are not formal proofs, and unsupported expressions should be reported rather than guessed.

## Interface refresh (v0.5)
- Light mode is now the default, with a bright white workspace, slate text, and clearer violet accents.
- Dark mode remains available and the selected theme continues to persist in the browser.
- Improved spacing, keyboard focus visibility, hover feedback, card depth, and mobile spacing.
- Updated the solver placeholder with concrete examples and added an accessible label.
- No solver/API behavior was intentionally changed.
