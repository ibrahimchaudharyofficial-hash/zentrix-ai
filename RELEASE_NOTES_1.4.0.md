# Zentrix AI 1.4.0

## Solver and science
- Added deterministic SI physics models: force, work, power, Ohm’s law, kinetic energy, gravitational potential energy, momentum, density, pressure, speed, and average acceleration.
- Physics commands use explicit named inputs to avoid guessing which quantities are given.
- Added numeric exponent magnitude enforcement to the safe AST parser.

## Learning Studio
- Added a local question generator for algebra, calculus, arithmetic, physics, geometry, and mixed practice.
- Added easy, medium, and hard difficulty settings.
- Added exact symbolic answer comparison; mathematically equivalent expressions are accepted.
- Added worked solution reveal using the existing SymPy engine.
- Added a searchable 21-item formula reference for algebra, calculus, geometry, physics, electricity, statistics, and probability.

## Verification transparency
- Every result now includes a verification level: symbolic, numerical, rule-based, failed, or unverified.
- The UI displays the kind of check rather than suggesting all checks are formal proofs.

## Photo question reader
- Added automatic image enlargement, grayscale conversion, and contrast enhancement before browser-side OCR.
- Shows Tesseract's confidence estimate alongside the reminder to review extracted text.
- Image processing remains in the browser; no image upload endpoint was added.

## Tests
- 40/40 core engine regression cases pass.
- 22/22 Class 10 coverage tests pass.
- Targeted word-problem, curriculum, expanded-school-math, Gemini-settings, and v1.4 feature tests pass.
- FastAPI health, physics solve, practice generation, answer verification, and HTML serving smoke tests pass.
- Frontend JavaScript syntax check passes.

## Limitations
- Physics commands assume SI units and do not infer dimensions or convert units.
- Practice generation is template-based, not an adaptive learning system.
- OCR is general printed-text OCR; handwriting and diagrams may be misread.
- The worked-solution panel is a guided local tutor, not a free-form AI chat tutor.
